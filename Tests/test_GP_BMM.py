###########################################################
# Tutorial example for trivariate BMM with a GP
###########################################################

#import packages
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

import pytest
from contextlib import contextmanager

#matplotlib settings for Latex plots
import matplotlib
matplotlib.rcParams.update({
    'font.family': 'serif',
    'text.usetex': True,
})

#import the SAMBA classes needed
from samba.models import Models, Uncertainties
from samba.discrepancy import Bivariate
from samba.gaussprocess import GP
from samba.fprdat import FPR

#define g and series expansions
g = np.linspace(1e-6,1.0,200)
ns = 3
nl = 3

#instantiate GP object for N_s = N_l = 3
obj1 = GP(g, ns, nl, kernel="Matern", nu=1.5, ci=68, error_model='informative')

##
#check ns, nl, g passing
@contextmanager
def does_not_raise():
    yield

@pytest.mark.parametrize(
    "g, ns, nl, expectation",
    [(g, ns, nl, does_not_raise()),],
)

def test_GP(g, ns, nl, expectation):
    with expectation:
        assert GP.gpredict == g 
        assert GP.loworder == ns
        assert GP.highorder == nl
##

#call the training() function from the GP() class
obj_tr1 = obj1.training(error=True, method=2, plot=True)

#TODO: check return object

#call the validate() function
mean1, sig1, cov1 = obj1.validate(plot=True)

#TODO: check mean1, sig1, cov1

#call plot_mix() to mix in the GP
mixed_mean, mixed_intervals = obj1.plot_mix(g, plot_fdagger=True, plot_true=True, GP_mean=mean1, GP_var=np.square(sig1))

#TODO: check returned variables

#call subplot_mix() and plot no GP results next to GP results
obj1.subplot_mix(g, GP_mean=mean1, GP_var=np.square(sig1))

#TODO: check figure generation

#calculate the Mahalanobis points
md_g, md_mean, md_sig, md_cov = obj1.MD_set(pts=3, plot=True)

#TODO: check each output

#use the points to calculate the Mahalanobis distance for our GP
md_gp, md_ref = obj1.md_squared(md_g, md_mean, md_cov, n_curves=1000)

#TODO: check return output

#call 
obj1.md_plotter(md_gp, md_ref, hist=True)

#TODO: check plotter for axes generation