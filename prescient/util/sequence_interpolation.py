#  ___________________________________________________________________________
#
#  Prescient
#  Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC
#  (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
#  Government retains certain rights in this software.
#  This software is distributed under the Revised BSD License.
#  ___________________________________________________________________________

'''Support for making a sequence of values appear to have values at a different frequency than what is stored.

Classes: InterpolatingSequence - wraps a sequence to make it appear as if data is provided at an alternate frequency
Functions: get_interpolated_index_position(), get_interpolatable_index_count()
'''

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple
import math

from prescient.util.math_utils import interpolate_between

class InterpolatedIndexPosition(NamedTuple):
    ''' Identifies a fractional position between two integer indices '''
    index_before:int
    index_after:int
    fraction_between:float


def get_interpolated_index_position(outer_index:int,
                                    units_at_outer_start:int,
                                    units_per_inner_index:int,
                                    units_per_outer_index:int) -> InterpolatedIndexPosition:
    ''' Find where an index from one sequence falls within another sequence.

    This method reconciles two sequences of values with different step lengths.
    For example, one series may have one data point every 15 minutes, and another
    every hour. One of these sequences is called the inner sequence, the other is 
    called the outer sequence.  This method takes an integer index from the outer
    sequence and indicates where it falls on the inner sequence, expressed as the 
    inner indices the point falls between, and the fractional position between the
    two indices.

    The inner and outer sequences don't have to start at the same time.  The
    units_at_outer_start indicates how much later the outer series starts compared
    to the inner series.

    Arguments
    ---------
    outer_index:int
        The index of the outer series that you want to located on the inner series
    units_at_outer_start:int
        How many time units after the inner series that the outer series starts
    units_per_inner_index:int
        The step length of the inner sequence
    units_per_outer_index:int
        The step length of the outer sequence

    Returns
    -------
    The location of the outer index on the inner sequence.  Note that it returns
    the logical position, which may be negative or exceed the length of the inner 
    sequence.  An outer index that falls directly on an inner index will have the
    same before and after index, and a fraction of 0.0.  Otherwise before and after
    will be sequential, and the fraction will be between 0.0 and 1.0.
    '''
    units_at_outer_index = units_at_outer_start + outer_index*units_per_outer_index
    fractional_index = units_at_outer_index / units_per_inner_index
    # Handle roundoff by snapping points close to an integer index
    index_before = int(math.floor(fractional_index + .0001))
    index_after = int(math.ceil(fractional_index - .0001))
    fraction = 0.0 if index_before == index_after \
               else fractional_index - index_before
    return InterpolatedIndexPosition(index_before, index_after, fraction)

def get_interpolatable_index_count(inner_count:int,
                                   units_at_outer_start:int,
                                   units_per_inner_index:int,
                                   units_per_outer_index:int):
    ''' When interpolating a sequence from one step size to another, get the number of
        steps the interpolated sequence will have.

    The sequence whose values will be interpolated is the inner sequence; the sequence
    that is generated via interpolation is the outer sequence.

    Only counts steps that can be interpolated from the inner sequence's value, with
    no extrapolation.

    Arguments
    ---------
    inner_count:int
        The number of values in the original (inner) sequence
    units_at_outer_start:int
        How many time units after the inner sequence starts that the outer sequence starts
    units_per_inner_index:int
        The time between each value in the inner sequence
    units_per_outer_index:int
        The time between each value in the sequence generated by interpolation
    '''
    # The duration from the start of the inner to the end of the last step of the inner.
    inner_units = inner_count * units_per_inner_index 
    # subtract off units before the outer sequence starts,
    # and make the final element the outer size instead of the inner size
    outer_units = inner_units - units_at_outer_start \
        - units_per_inner_index + units_per_outer_index 
    outer_len = outer_units / units_per_outer_index
    return max(0, math.floor(outer_len + .0001))

class InterpolatingSequence(Sequence):
    ''' A list-like class that makes time series data appear to occur
        more or less frequently than an underlying sequence, using
        interpolation when necessary.

        For example, a list might have one value every 60 minutes.  You can
        use an InterpolatingSequence to present this list as if it had one
        value every 15 minutes.  The InterpolatingSequence will be four times
        as long as the original list (almost, see below).  Values on the 
        hour will be taken from the original list, while other values 
        are interpolated.  If the original list is [1,5,9], the InterpolatingSequence 
        is [1,2,3,4,5,6,7,8,9].

        Note that in our example, the InterpolatingSequence is less than four 
        times the original list size because the final element in the original list
        ends the InterpolatingSequence; it isn't chopped into 4 like the other elements.
        The InterpolatingSequence will include all indices that start within the
        range of the original list, including its endpoints.  It will not include
        elements that begin after the start of the original list's final element,
        not even those that fall entirely within the final element's time range, as
        there is no subsequent value to use for interpolation.

        It is possible to start the InterpolatingSequence somewhere after the beginning
        of the original list.  The resulting elements will skip and interpolate initial
        values in the original list as appropriate.  For example, consider this 
        InterpolatingSequence that starts 30 minutes after the original sequence:

            >>> seq = InterpolatingSequence([1,5], 60, 15, 30)
            >>> str(seq)
            '[3.0, 4.0, 5]'
    '''
    
    def __init__(self, inner_sequence:Sequence,
                 units_per_inner_index:int,
                 units_per_outer_index:int,
                 units_at_outer_start:int):
        '''  Constructor

        Arguments
        ---------
        inner_sequence:Sequence
            A list or other sequence that will be interpolated
        units_per_inner_index: int
            The number of minutes (or other units) between each value in the inner_sequence
        units_per_outer_index:int
            The number of minutes (or other units) the InterpolatingSequence will appear to have between each value
        units_at_outer_start:int
            The number of minutes (or other units) at start of the inner_sequence that should not be included
            in the IterpolatingSequence
        '''
        self.inner_sequence = inner_sequence
        self.units_per_inner_index = units_per_inner_index
        self.units_at_outer_start = units_at_outer_start
        self.units_per_outer_index = units_per_outer_index

    def __len__(self) -> int:
        return get_interpolatable_index_count(len(self.inner_sequence),
                                              self.units_at_outer_start,
                                              self.units_per_inner_index,
                                              self.units_per_outer_index)

    def __getitem__(self, index:int):
        idx = get_interpolated_index_position(index, 
                                              self.units_at_outer_start,
                                              self.units_per_inner_index,
                                              self.units_per_outer_index)
        # Patch in try/excepts so we can do SCED in the last hour of the day
        try:
            v1 = self.inner_sequence[idx.index_before]
        except IndexError:
            v1 = self.inner_sequence[len(self.inner_sequence)-1]
        try:
            v2 = self.inner_sequence[idx.index_after]
        except:
            v2 = self.inner_sequence[len(self.inner_sequence)-1]
        return interpolate_between(v1, v2, idx.fraction_between)

    def __str__(self) -> str:
        ''' Generate a string with this sequence's values '''
        return f"[{', '.join(str(self[i]) for i in range(len(self)))}]"

    def __repr__(self) -> str:
        return f"InterpolatingSequence({self.inner_sequence.__repr__()}, " \
               f"{self.units_per_inner_index}, {self.units_per_exposed_index}, " \
               f"{self.units_at_exposed_start})"
