#  ___________________________________________________________________________
#
#  Prescient
#  Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC
#  (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
#  Government retains certain rights in this software.
#  This software is distributed under the Revised BSD License.
#  ___________________________________________________________________________

## file for power and reserve variables
from __future__ import division
from pyomo.environ import *
import math
import six 

from prescient.model_components.decorators import add_model_attr 
component_name = 'non_dispatchable_vars'

## file non-dispatchable power -- determined by .dat file
@add_model_attr(component_name, requires = {'data_loader': None, })
def file_non_dispatchable_vars(model):

    # assume wind can be curtailed, then wind power is a decision variable
    def nd_bounds_rule(m,n,t):
        return (m.MinNondispatchablePower[n,t], m.MaxNondispatchablePower[n,t])
    model.NondispatchablePowerUsed = Var(model.AllNondispatchableGenerators, model.TimePeriods, within=NonNegativeReals, bounds=nd_bounds_rule)

    return