import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from .models import Models, Uncertainties

__all__ = ['Bivariate']


class Bivariate(Models, Uncertainties):

    def __init__(self, loworder, highorder, error_model='informative', ci=68):

        r'''
        The bivariate BMM method used to construct the mixed model of two series
        expansions. This class contains the fdagger function and the plotter.

        Example:
            Bivariate(loworder=5, highorder=10)

        Parameters:
            loworder (numpy.ndarray, int, float): The value of N_s to be 
                used to truncate the small-g expansion.

            highorder (numpy.ndarray, int, float): The value of N_l to be 
                used to truncate the large-g expansion.

            error_model (str): The error model to be used in the calculation. 
                Options are 'uninformative' and 'informative'. Default is 'informative'. 
            
            ci (int): The value of the credibility interval desired (can be 68 or 95).

        Returns:
            None.
        '''

        #get interval
        self.ci = ci
        
        #instantiate the Uncertainties class and error model
        self.u = Uncertainties(error_model)
        self.error_model = self.u.error_model

        #check type and assign class variables
        if isinstance(loworder, float) == True or isinstance(loworder, int) == True:
            loworder = np.array([loworder])
        
        if isinstance(highorder, float) == True or isinstance(highorder, int) == True:
            highorder = np.array([highorder])

        self.loworder = loworder 
        self.highorder = highorder

        #instantiate Models() class here
        self.m = Models(self.loworder, self.highorder)

        return None

    
    def fdagger(self, g): 

        r'''
        A do-it-all function to determine the pdf of the mixed model. Can use models 
        indicated by inputting arrays into the loworder and highorder variables.

        Example:
            Bivariate.fdagger(g=np.linspace(1e-6, 0.5, 100))

        Parameters:
            g (numpy.linspace): The linspace over which this calculation is performed.
            
        Returns:
            mean (numpy.ndarray): The mixed model mean (either including a GP or not 
                depending on the function arguments).
            
            intervals (numpy.ndarray): The credibility interval of the mixed model mean.
            
            interval_low (numpy.ndarray): The variance interval for the small-g expansion 
                (calculated from the next order after the truncation). 

            interval_high (numpy.ndarray): The variance interval for the large-g expansion 
                (calculated from the next order after the truncation).
        '''

        #check type
        if isinstance(self.loworder, float) == True or isinstance(self.loworder, int) == True:
            self.loworder = np.array([self.loworder])
        
        if isinstance(self.highorder, float) == True or isinstance(self.highorder, int) == True:
            self.highorder = np.array([self.highorder])

        #uncertainties
        v_low = np.asarray([self.u.variance_low(g, self.loworder[i]) for i in range(len(self.loworder))])
        v_high = np.asarray([self.u.variance_high(g, self.highorder[i]) for i in range(len(self.highorder))])

        #calculating models
        f_low = np.asarray([self.m.low_g(g)[i,:] for i in range(len(self.loworder))])
        f_high = np.asarray([self.m.high_g(g)[i,:] for i in range(len(self.highorder))])

        # concatenate models
        f = np.concatenate((f_low, f_high), axis=0)
        v = np.concatenate((v_low, v_high), axis=0)

        #initialise arrays
        mean_n = np.zeros([len(f), len(g)])
        mean_d = np.zeros([len(f), len(g)])
        mean = np.zeros([len(g)])
        var = np.zeros([len(f), len(g)])
            
        #create fdagger for each value of g
        for i in range(len(f)):
            mean_n[i] = f[i]/v[i]
            mean_d[i] = 1.0/v[i]
            var[i] = 1.0/v[i]

        #save variances for each model
        self.var_weights = var/(np.sum(var, axis=0))
        
        mean_n = np.sum(mean_n, axis=0)
        mean_d = np.sum(mean_d, axis=0)

        #mean, variance calculation
        mean = mean_n/mean_d
        var = 1.0/np.sum(var, axis=0)

        #which credibility interval to use
        if self.ci == 68:
            val = 1.0
        elif self.ci == 95:
            val = 1.96
        else:
            raise ValueError('Please enter either 68 or 95.')

        #initialise credibility intervals
        intervals = np.zeros([len(g), 2])
        interval_low = np.zeros([len(self.loworder), len(g), 2])
        interval_high = np.zeros([len(self.highorder), len(g), 2])

        #calculate credibility intervals
        intervals[:, 0] = (mean - val * np.sqrt(var))
        intervals[:, 1] = (mean + val * np.sqrt(var))

        for i in range(len(self.loworder)):
            interval_low[i,:,0] = (self.m.low_g(g)[i,:] - val * np.sqrt(v_low[i,:]))
            interval_low[i,:,1] = (self.m.low_g(g)[i,:] + val * np.sqrt(v_low[i,:]))
         
        for i in range(len(self.highorder)):
            interval_high[i,:,0] = (self.m.high_g(g)[i,:] - val * np.sqrt(v_high[i,:]))
            interval_high[i,:,1] = (self.m.high_g(g)[i,:] + val * np.sqrt(v_high[i,:]))

        return mean, intervals, interval_low, interval_high

    # fix this for the GP case
    def plot_mix(self, g, plot_fdagger=True, plot_true=True):

        r'''
        An all-in-one plotting function that will plot the results of fdagger for N numbers
        of models, the next orders of the expansion models, and the validation step of the 
        model mixing in fdagger to test fdagger results.

        Example:
            Bivariate.plot_mix(g=np.linspace(1e-6, 0.5, 100), plot_fdagger=True)

        Parameters:
            g (numpy.linspace): The space over which the models are calculated.
        
            plot_fdagger (bool): If True, this parameter will allow for the 
                plotting of fdagger and its credibility interval. 
            
            plot_true (bool): Determines whether or not to plot the true model curve. 
                Default is True.

        Returns:
            mean (numpy.ndarray): The mean of the mixed model at each point in g.

            intervals (numpy.ndarray): The values of the credibility intervals at each
                point in g. 
        '''

        #set up plot configuration
        fig = plt.figure(figsize=(8,6), dpi=600)
        ax = plt.axes()
        ax.tick_params(axis='x', labelsize=18)
        ax.tick_params(axis='y', labelsize=18)
        ax.locator_params(nbins=8)
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())

        #set up x and y limits
        ax.set_xlim(0.0,1.0)
       # ax.set_xlim(0.0,0.5)
        ax.set_ylim(1.2,3.2)
       # ax.set_ylim(1.0,3.0)
        ax.set_yticks([1.2, 1.6, 2.0, 2.4, 2.8, 3.2])
      #  ax.set_ylim(2.0,2.8)
       # ax.set_yticks([2.0, 2.2, 2.4, 2.6, 2.8])
     
        #labels and true model
        ax.set_xlabel('g', fontsize=22)
        ax.set_ylabel('F(g)', fontsize=22)

        if plot_true is True:
            ax.plot(g, self.m.true_model(g), 'k', label='True model')

        # call fdagger to calculate results
        mean, intervals, interval_low, interval_high = self.fdagger(g)

        # plot the small-g expansions and error bands
        for i,j in zip(range(len(self.loworder)), self.loworder):
            ax.plot(g, self.m.low_g(g)[i,:], 'r--', label=r'$f_s$ ($N_s$ = {})'.format(j))
        
        for i in range(len(self.loworder)):
            ax.plot(g, interval_low[i, :, 0], 'r', linestyle='dotted', \
                label=r'$f_s$ ($N_s$ = {}) {}\% CI'.format(self.loworder[i], int(self.ci)))
            ax.plot(g, interval_low[i, :, 1], 'r', linestyle='dotted')

        # for each large-g order, calculate and plot
        for i,j in zip(range(len(self.highorder)), self.highorder):
            ax.plot(g, self.high_g(g)[i,:], 'b--', label=r'$f_l$ ($N_l$ = {})'.format(j))
          
        for i in range(len(self.highorder)):
            ax.plot(g, interval_high[i, :, 0], 'b', linestyle='dotted', \
                label=r'$f_l$ ($N_l$ = {}) {}\% CI'.format(self.highorder[i], int(self.ci)))
            ax.plot(g, interval_high[i, :, 1], 'b', linestyle='dotted')
            
        if plot_fdagger == True:
            ax.plot(g, mean, 'g', label='Mean')
            ax.plot(g, intervals[:,0], 'g', linestyle='dotted', label=r'{}$\%$ CI'.format(int(self.ci)))
            ax.plot(g, intervals[:,1], 'g', linestyle='dotted')
            ax.fill_between(g, intervals[:,0], intervals[:,1], color='green', alpha=0.2)
        
        ax.legend(fontsize=16, loc='upper right')
        plt.show()

        # #save figure option
        # response = input('Would you like to save this figure? (yes/no)')

        # if response == 'yes':
        #     name = input('Enter a file name (include .jpg, .png, etc.)')
        #     fig.savefig(name, bbox_inches='tight')

        return mean, intervals 
        

    def plot_error_models(self, g): 

        r'''
        A plotter to compare the uninformative error model results of two models 
        to the informative error model results for the same two models. Panel a
        refers to the uninformative error model panel in the subplot, and panel b
        corresponds to the informative error model panel. 

        Example:
            Bivariate.plot_error_models(g=np.linspace(1e-6, 0.5, 100))

        Parameters:
            g (numpy.linspace): The space over which the models are calculated.

        Returns:
            None.
        '''

        #set up plot configuration        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16,6), dpi=600, sharex=True, sharey=True, \
                         gridspec_kw={'hspace':0, 'wspace':0}, \
                         tight_layout=True)
      
        for ax in (ax1, ax2):
            ax.tick_params(axis='both', which='major', labelsize=20, right=True, top=True, length=6)
            ax.tick_params(axis='both', which='minor', labelsize=20, right=True, top=True, length=3)
            ax.locator_params(nbins=5)
            ax.xaxis.set_minor_locator(AutoMinorLocator())
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            ax.set_xlim(0.0,1.0)
            ax.set_xticks([0.1, 0.3, 0.5, 0.7, 0.9])
            ax.set_ylim(1.0,3.0)
         
            #labels and true model
            ax.set_xlabel('g', fontsize=24)
            ax.set_ylabel('F(g)', fontsize=24)
            ax.plot(g, self.m.true_model(g), 'k', label='True model')

            #only label outer plot axes
            ax.label_outer()
            
        #call fdagger to calculate results (overwrite class variable)
        self.u = Uncertainties(error_model='uninformative')
        self.error_model = self.u.error_model
        mean_u, intervals_u, interval_low_u, interval_high_u = self.fdagger(g)
        self.u = Uncertainties(error_model='informative')
        self.error_model = self.u.error_model 
        mean_i, intervals_i, interval_low_i, interval_high_i = self.fdagger(g)

        #plot the small-g expansions and error bands (panel a)
        ax1.plot(g, self.m.low_g(g)[0,:], 'r--', \
            label=r'$f_s$ ($N_s$ = {})'.format(self.loworder[0]))
        ax1.plot(g, interval_low_u[0, :, 0], 'r', linestyle='dotted',\
             label=r'$f_s$ ($N_s$ = {}) {}\% CI'.format(self.loworder[0], int(self.ci)))
        ax1.plot(g, interval_low_u[0, :, 1], 'r', linestyle='dotted')

        #plot the small-g expansions and error bands (panel b)
        ax2.plot(g, self.m.low_g(g)[0,:], 'r--', label=r'$f_s$ ($N_s$ = {})'.format(self.loworder[0]))
        ax2.plot(g, interval_low_i[0, :, 0], 'r', linestyle='dotted',\
                label=r'$f_s$ {}\% CI'.format(int(self.ci)))
        ax2.plot(g, interval_low_i[0, :, 1], 'r', linestyle='dotted')

        #plot the large-g expansions and error bands (panel a)
        ax1.plot(g, self.m.high_g(g)[0,:], 'b--', label=r'$f_l$ ($N_l$ = {})'.format(self.highorder[0]))
        ax1.plot(g, interval_high_u[0, :, 0], 'b', linestyle='dotted', label=r'$f_l$ {}\% CI'.format(int(self.ci)))
        ax1.plot(g, interval_high_u[0, :, 1], 'b', linestyle='dotted')

        #plot the large-g expansions and error bands (panel b)
        ax2.plot(g, self.m.high_g(g)[0,:], 'b--', label=r'$f_l$ ($N_l$ = {})'.format(self.highorder[0]))
        ax2.plot(g, interval_high_i[0, :, 0], 'b', linestyle='dotted', \
            label=r'$f_l$ {}\% CI'.format(int(self.ci)))
        ax2.plot(g, interval_high_i[0, :, 1], 'b', linestyle='dotted')

        #PPD (panel a)
        ax1.plot(g, mean_u, 'g', label='Mixed model')
        ax1.plot(g, intervals_u[:,0], 'g', linestyle='dotted', label=r'{}$\%$ CI'.format(int(self.ci)))
        ax1.plot(g, intervals_u[:,1], 'g', linestyle='dotted')
        ax1.fill_between(g, intervals_u[:,0], intervals_u[:,1], color='green', alpha=0.2)

        #PPD (panel b)
        ax2.plot(g, mean_i, 'g', label='Mixed model')
        ax2.plot(g, intervals_i[:,0], 'g', linestyle='dotted', label=r'{}$\%$ CI'.format(int(self.ci)))
        ax2.plot(g, intervals_i[:,1], 'g', linestyle='dotted')
        ax2.fill_between(g, intervals_i[:,0], intervals_i[:,1], color='green', alpha=0.2)

        #ax2.legend(bbox_to_anchor=(1.0, 0.5), fontsize=16, loc='center left')
        ax2.legend(fontsize=16, loc='upper right')

        #label panels
        ax1.text(0.94, 1.1, '(a)', fontsize=20)
        ax2.text(0.94, 1.1, '(b)', fontsize=20)

        plt.show()

        # save figure option
        response = input('Would you like to save this figure? (yes/no)')

        if response == 'yes':
            name = input('Enter a file name (include .jpg, .png, etc.)')
            fig.savefig(name, bbox_inches='tight')

        return None


    def vertical_plot_fdagger(self, g1, g2, gp_dict=None, gp_dict2=None, gp_points=None, gp_points2=None, low_orders=None, high_orders=None):

        r'''
        Vertical panel plotter for the paper to generate two mixed model plots. 

        Example:
            Bivariate.vertical_plot_fdagger(g1=np.linspace(1e-6, 0.5, 100), g2=np.linspace(1e-6,1.0,100),
            gp_mean1=np.array([]), gp_mean2=np.array([]), gp_var1=np.array([,]), gp_var2=np.array([,]))

        Parameters:
            g1 (numpy.linspace): The space over which the models (and GP) were calculated 
                for panel a. 

            g2 (numpy.linspace): The space over which the models (and GP) were calculated 
                for panel b. 

            gp_mean1 (numpy.ndarray): GP mean results to be mixed with the models in panel a. 
                Optional. 

            gp_mean2 (numpy.ndarray): GP mean results to be mixed with the models in panel b. 
                Optional.

            gp_var1 (numpy.ndarray): GP variance results for panel a. Optional.

            gp_var2 (numpy.ndarray): GP variance results for panel b. Optional. 
      
        Returns:
            None.
        '''

        #set up plot configuration
        fig = plt.figure(figsize=(8,12), dpi=600)
        gs = fig.add_gridspec(2,1, hspace=0, wspace=0)
        (ax1, ax2) = gs.subplots(sharex=True, sharey=True)
       
        for ax in (ax1, ax2):

            ax.tick_params(axis='x', right=True, which='both', labelsize=18)
            ax.tick_params(axis='y', top=True, which='both', labelsize=18)
            ax.locator_params(nbins=5)
            ax.xaxis.set_minor_locator(AutoMinorLocator())
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            ax.set_xlim(0.0,1.0)
            ax.set_ylim(1.2,3.2)
            ax.set_yticks([1.4, 1.8, 2.2, 2.6, 3.0])

            #labels and true model
            ax.set_xlabel('g', fontsize=22)
            ax.set_ylabel('F(g)', fontsize=22)
            ax.plot(g1, self.m.true_model(g1), 'k', label='True model')

            #only label outer plot axes
            ax.label_outer()

        #copy class variables to force changes
        if low_orders is None and high_orders is None:
            loworder = self.loworder.copy()
            highorder = self.highorder.copy()
        else:
            loworder = low_orders
            highorder = high_orders
            self.loworder = loworder
            self.highorder = highorder
        
       # else:
        #mixed results (panel a)
        self.loworder = np.array([loworder[0]])
        self.highorder = np.array([highorder[0]])
        self.m = Models(self.loworder, self.highorder)
        mean_1, intervals_1, interval_low_1, interval_high_1 = self.fdagger(g1)

        #mixed results (panel b)
        self.loworder = np.array([loworder[1]])
        self.highorder = np.array([highorder[1]])
        self.m = Models(self.loworder, self.highorder)
        mean_2, intervals_2, interval_low_2, interval_high_2 = self.fdagger(g2)

        #plot the small-g expansions and error bands (panel a)
        self.loworder = np.array([loworder[0]])
        self.m = Models(self.loworder, self.highorder)
        ax1.plot(g1, self.m.low_g(g1)[0,:], 'r--', \
            label=r'$f_s$ ($N_s$ = {})'.format(self.loworder[0]))
        ax1.plot(g1, interval_low_1[0, :, 0], 'r', linestyle='dotted',\
             label=r'$f_s$ {}\% CI'.format(int(self.ci)))
        ax1.plot(g1, interval_low_1[0, :, 1], 'r', linestyle='dotted')

        #plot the small-g expansions and error bands (panel b)
        self.loworder = np.array([loworder[1]])
        self.m = Models(self.loworder, self.highorder)
        ax2.plot(g2, self.m.low_g(g2)[0,:], color='r', linestyle='dashed',\
                label=r'$f_s$ ($N_s$ = {})'.format(self.loworder[0]))
        ax2.plot(g2, interval_low_2[0, :, 0], color='r', linestyle='dotted', \
            label=r'$f_s$ {}\% CI'.format(int(self.ci)))
        ax2.plot(g2, interval_low_2[0, :, 1], color='r', linestyle='dotted')

        #plot the large-g expansions and error bands (panel a)
        self.highorder = np.array([highorder[0]])
        self.m = Models(self.loworder, self.highorder)
        ax1.plot(g1, self.m.high_g(g1)[0,:], 'b--', label=r'$f_l$ ($N_l$ = {})'.format(self.highorder[0]))
        ax1.plot(g1, interval_high_1[0, :, 0], 'b', linestyle='dotted', label=r'$f_l$ {}\% CI'.format(int(self.ci)))
        ax1.plot(g1, interval_high_1[0, :, 1], 'b', linestyle='dotted')
       
        #plot the large-g expansions and error bands (panel b)
        self.highorder = np.array([highorder[1]])
        self.m = Models(self.loworder, self.highorder)
        ax2.plot(g2, self.m.high_g(g2)[0,:], color='b', linestyle='dashed', \
                label=r'$f_l$ ($N_l$ = {})'.format(self.highorder[0]))
        ax2.plot(g2, interval_high_2[0, :, 0], color='b', linestyle='dotted', \
            label=r'$f_l$ {}\% CI'.format(int(self.ci)))
        ax2.plot(g2, interval_high_2[0, :, 1], color='b', linestyle='dotted')

        # error bar option
        if gp_points is not None:
            ax1.errorbar(gp_points['gs'], gp_points['datas'], yerr=gp_points['sigmas'], color="red", fmt='o', markersize=4, \
                capsize=4, label=r"Training data", zorder=10)
            
        if gp_points2 is not None:
            ax2.errorbar(gp_points2['gs'], gp_points2['datas'], yerr=gp_points2['sigmas'], color="red", fmt='o', markersize=4, \
                capsize=4, label=r"Training data", zorder=10)
           
        #uninformative model case
        if gp_dict is None:
            ax1.plot(g1, mean_1, 'g', label='Mixed model')
            ax1.plot(g1, intervals_1[:,0], 'g', linestyle='dotted', label=r'{}$\%$ CI'.format(int(self.ci)))
            ax1.plot(g1, intervals_1[:,1], 'g', linestyle='dotted')
            ax1.fill_between(g1, intervals_1[:,0], intervals_1[:,1], color='green', alpha=0.2)
        else:
            ax1.plot(gp_dict['g'], gp_dict['mean'], 'g', label='Mixed model')
            ax1.plot(gp_dict['g'], gp_dict['mean']-gp_dict['std'], 'g', linestyle='dotted', label=r'{}$\%$ CI'.format(int(self.ci)))
            ax1.plot(gp_dict['g'], gp_dict['mean']+gp_dict['std'], 'g', linestyle='dotted')
            ax1.fill_between(gp_dict['g'], gp_dict['mean']-gp_dict['std'], gp_dict['mean']+gp_dict['std'], color='green', alpha=0.2)

        #informative model case
        if gp_dict2 is None:
            ax2.plot(g2, mean_2, 'g', label='Mixed model')
            ax2.plot(g2, intervals_2[:,0], 'g', linestyle='dotted', label=r'{}$\%$ CI'.format(int(self.ci)))
            ax2.plot(g2, intervals_2[:,1], 'g', linestyle='dotted')
            ax2.fill_between(g2, intervals_2[:,0], intervals_2[:,1], color='green', alpha=0.2)
        else:
            ax2.plot(gp_dict2['g'], gp_dict2['mean'], 'g', label='Mixed model')
            ax2.plot(gp_dict2['g'], gp_dict2['mean']-gp_dict2['std'], 'g', linestyle='dotted', label=r'{}$\%$ CI'.format(int(self.ci)))
            ax2.plot(gp_dict2['g'], gp_dict2['mean']+gp_dict2['std'], 'g', linestyle='dotted')
            ax2.fill_between(gp_dict2['g'], gp_dict2['mean']-gp_dict2['std'], gp_dict2['mean']+gp_dict2['std'], color='green', alpha=0.2)

        #add panel labels
        ax1.text(0.94, 1.3, '(a)', fontsize=18)
        ax2.text(0.94, 1.3, '(b)', fontsize=18)

        ax2.legend(fontsize=18, loc='upper right')
        ax1.legend(fontsize=18, loc='upper right')
        plt.show()

        #save figure option
        response = input('Would you like to save this figure? (yes/no)')

        if response == 'yes':
            name = input('Enter a file name (include .jpg, .png, etc.)')
            fig.savefig(name, bbox_inches='tight')
    
        return None
    
    
    def horizontal_plot_fdagger(self, g1, g2, gp_dict=None, gp_dict2=None, gp_points=None, gp_points2=None, low_orders=None, high_orders=None):

        r'''
        Horizontal panel plotter for the paper to generate two mixed model plots. 

        Example:
            Bivariate.horizontal_plot_fdagger(g1=np.linspace(1e-6, 0.5, 100), g2=np.linspace(1e-6,1.0,100),
            gp_mean1=np.array([]), gp_mean2=np.array([]), gp_var1=np.array([,]), gp_var2=np.array([,]))

        Parameters:
            g1 (numpy.linspace): The space over which the models (and GP) were calculated 
                for panel a. 

            g2 (numpy.linspace): The space over which the models (and GP) were calculated 
                for panel b. 

            gp_mean1 (numpy.ndarray): GP mean results to be mixed with the models in panel a. 
                Optional. 

            gp_mean2 (numpy.ndarray): GP mean results to be mixed with the models in panel b. 
                Optional.

            gp_var1 (numpy.ndarray): GP variance results for panel a. Optional.

            gp_var2 (numpy.ndarray): GP variance results for panel b. Optional. 
      
        Returns:
            None.
        '''

        #set up plot configuration        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16,6), dpi=600, sharex=True, sharey=True, \
                         gridspec_kw={'hspace':0, 'wspace':0}, \
                         tight_layout=True)
      
        for ax in (ax1, ax2):
            ax.tick_params(axis='both', which='major', labelsize=20, right=True, top=True, length=6)
            ax.tick_params(axis='both', which='minor', labelsize=20, right=True, top=True, length=3)
            ax.locator_params(nbins=5)
            ax.xaxis.set_minor_locator(AutoMinorLocator())
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            ax.set_xlim(0.0,1.0)
            ax.set_xticks([0.1, 0.3, 0.5, 0.7, 0.9])
            ax.set_ylim(1.0,3.0)
         
            #labels and true model
            ax.set_xlabel('g', fontsize=24)
            ax.set_ylabel('F(g)', fontsize=24)
            ax.plot(g1, self.m.true_model(g1), 'k', label='True model')

            #only label outer plot axes
            ax.label_outer()

        #copy class variables to force changes
        if low_orders is None and high_orders is None:
            loworder = self.loworder.copy()
            highorder = self.highorder.copy()
        else:
            loworder = low_orders
            highorder = high_orders
            self.loworder = loworder
            self.highorder = highorder
 
        #mixed results (panel a)
        self.loworder = np.array([loworder[0]])
        self.highorder = np.array([highorder[0]])
        self.m = Models(self.loworder, self.highorder)
        mean_1, intervals_1, interval_low_1, interval_high_1 = self.fdagger(g1)

        #mixed results (panel b)
        self.loworder = np.array([loworder[1]])
        self.highorder = np.array([highorder[1]])
        self.m = Models(self.loworder, self.highorder)
        mean_2, intervals_2, interval_low_2, interval_high_2 = self.fdagger(g2)

        #plot the small-g expansions and error bands (panel a)
        self.loworder = np.array([loworder[0]])
        self.m = Models(self.loworder, self.highorder)
        ax1.plot(g1, self.m.low_g(g1)[0,:], 'r--', \
            label=r'$f_s$ ($N_s$ = {})'.format(self.loworder[0]))
        ax1.plot(g1, interval_low_1[0, :, 0], 'r', linestyle='dotted',\
             label=r'$f_s$ {}\% CI'.format(int(self.ci)))
        ax1.plot(g1, interval_low_1[0, :, 1], 'r', linestyle='dotted')

        #plot the small-g expansions and error bands (panel b)
        self.loworder = np.array([loworder[1]])
        self.m = Models(self.loworder, self.highorder)
        ax2.plot(g2, self.m.low_g(g2)[0,:], color='r', linestyle='dashed',\
                label=r'$f_s$ ($N_s$ = {})'.format(self.loworder[0]))
        ax2.plot(g2, interval_low_2[0, :, 0], color='r', linestyle='dotted', \
            label=r'$f_s$ {}\% CI'.format(int(self.ci)))
        ax2.plot(g2, interval_low_2[0, :, 1], color='r', linestyle='dotted')

        #plot the large-g expansions and error bands (panel a)
        self.highorder = np.array([highorder[0]])
        self.m = Models(self.loworder, self.highorder)
        ax1.plot(g1, self.m.high_g(g1)[0,:], 'b--', label=r'$f_l$ ($N_l$ = {})'.format(self.highorder[0]))
        ax1.plot(g1, interval_high_1[0, :, 0], 'b', linestyle='dotted', label=r'$f_l$ {}\% CI'.format(int(self.ci)))
        ax1.plot(g1, interval_high_1[0, :, 1], 'b', linestyle='dotted')
       
        #plot the large-g expansions and error bands (panel b)
        self.highorder = np.array([highorder[1]])
        self.m = Models(self.loworder, self.highorder)
        ax2.plot(g2, self.m.high_g(g2)[0,:], color='b', linestyle='dashed', \
                label=r'$f_l$ ($N_l$ = {})'.format(self.highorder[0]))
        ax2.plot(g2, interval_high_2[0, :, 0], color='b', linestyle='dotted', \
            label=r'$f_l$ {}\% CI'.format(int(self.ci)))
        ax2.plot(g2, interval_high_2[0, :, 1], color='b', linestyle='dotted')

        # error bar option
        if gp_points is not None:
            ax1.errorbar(gp_points['gs'], gp_points['datas'], yerr=gp_points['sigmas'], color="red", fmt='o', markersize=4, \
                capsize=4, label=r"Training data", zorder=10)
            
        if gp_points2 is not None:
            ax2.errorbar(gp_points2['gs'], gp_points2['datas'], yerr=gp_points2['sigmas'], color="red", fmt='o', markersize=4, \
                capsize=4, label=r"Training data", zorder=10)
           
        #uninformative model case
        if gp_dict is None:
            ax1.plot(g1, mean_1, 'g', label='Mixed model')
            ax1.plot(g1, intervals_1[:,0], 'g', linestyle='dotted', label=r'{}$\%$ CI'.format(int(self.ci)))
            ax1.plot(g1, intervals_1[:,1], 'g', linestyle='dotted')
            ax1.fill_between(g1, intervals_1[:,0], intervals_1[:,1], color='green', alpha=0.2)
        else:
            ax1.plot(gp_dict['g'], gp_dict['mean'], 'g', label='Mixed model')
            ax1.plot(gp_dict['g'], gp_dict['mean']-gp_dict['std'], 'g', linestyle='dotted', label=r'{}$\%$ CI'.format(int(self.ci)))
            ax1.plot(gp_dict['g'], gp_dict['mean']+gp_dict['std'], 'g', linestyle='dotted')
            ax1.fill_between(gp_dict['g'], gp_dict['mean']-gp_dict['std'], gp_dict['mean']+gp_dict['std'], color='green', alpha=0.2)

        #informative model case
        if gp_dict2 is None:
            ax2.plot(g2, mean_2, 'g', label='Mixed model')
            ax2.plot(g2, intervals_2[:,0], 'g', linestyle='dotted', label=r'{}$\%$ CI'.format(int(self.ci)))
            ax2.plot(g2, intervals_2[:,1], 'g', linestyle='dotted')
            ax2.fill_between(g2, intervals_2[:,0], intervals_2[:,1], color='green', alpha=0.2)
        else:
            ax2.plot(gp_dict2['g'], gp_dict2['mean'], 'g', label='Mixed model')
            ax2.plot(gp_dict2['g'], gp_dict2['mean']-gp_dict2['std'], 'g', linestyle='dotted', label=r'{}$\%$ CI'.format(int(self.ci)))
            ax2.plot(gp_dict2['g'], gp_dict2['mean']+gp_dict2['std'], 'g', linestyle='dotted')
            ax2.fill_between(gp_dict2['g'], gp_dict2['mean']-gp_dict2['std'], gp_dict2['mean']+gp_dict2['std'], color='green', alpha=0.2)

        #add panel labels
        ax1.text(0.94, 1.1, '(a)', fontsize=20)
        ax2.text(0.94, 1.1, '(b)', fontsize=20)

        ax2.legend(fontsize=16, loc='upper right')
        ax1.legend(fontsize=16, loc='upper right')
        plt.show()

        #save figure option
        response = input('Would you like to save this figure? (yes/no)')

        if response == 'yes':
            name = input('Enter a file name (include .jpg, .png, etc.)')
            fig.savefig(name, bbox_inches='tight')
    
        return None
