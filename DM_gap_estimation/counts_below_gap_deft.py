# PACKAGE IMPORT
import numpy as np
import scipy as sp
import pandas as pd
from pandas import DataFrame as df
import random
import matplotlib
from matplotlib import rcParams
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import KernelDensity
from DM_definitions import DM_known_draws, make_pdf, make_kde_funtion
from DM_kde_gen import DM_grid, DM_frb, DM_rand_draws
import suftware as sw
import warnings
import seaborn as sns
sns.set()
sns.set_style('darkgrid')
sns.set_context('poster')
rcParams['figure.figsize'] = 22,11
matplotlib.rc('xtick', labelsize=18) 
matplotlib.rc('ytick', labelsize=18) 

num_kde_samples = 1000
DM_stepsize = 0.1

deft_sample_1000 = np.asarray(random.sample(list(DM_rand_draws),1000))
deft_density_1000 = sw.DensityEstimator(deft_sample_1000, alpha=4)
deft_density_obs = sw.DensityEstimator(DM_known_draws, alpha=4)

# Evaluate optimal density
deft_optimal_1000 = deft_density_1000.evaluate(DM_grid)
deft_optimal_obs = deft_density_obs.evaluate(DM_grid)

"PDF made from DEFT with 1000 draws"
# Write PDF of optimal function, then take draws
DM_deft_rand = make_pdf(distribution=deft_optimal_1000,num_of_draws=num_kde_samples,grid=DM_grid,stepsize=DM_stepsize)
DM_deft_draws_rand = DM_deft_rand[0]
DM_deft_rand_distribution  = DM_deft_rand[1]

count_deft_rand = 0
for i in DM_deft_draws_rand: 
    if i < 100: 
        count_deft_rand = count_deft_rand + 1

plt.plot(DM_grid,DM_deft_rand_distribution*500)
sns.distplot(DM_deft_draws_rand, hist = True, kde = False, rug = True, bins=300,
             color = 'darkblue', 
             kde_kws={'linewidth': 2, 'bw':99},
             rug_kws={'color': 'red'})
plt.axvline(x=100,linewidth=2,linestyle='dashed',label='Simulated gap value',color='k')
plt.title('{}/1000 draws fall below simulated gap'.format(count_deft_rand),fontsize=40)
plt.xlabel('$DM_{DEFT}$ Simulated', fontsize=28)
plt.ylabel('PDF', fontsize=28)
plt.legend(fontsize=28)
plt.xlim(0,1800)
plt.tight_layout()
plt.savefig('DM_outputs/Counts_below_gap/DEFT_counts.png')
plt.show()

"PDF made from Observed"
#!! Doesn't mean anything really - don't know true gap value so
# Write PDF of optimal function, then take draws
DM_deft_obs = make_pdf(distribution=deft_optimal_obs/np.sum(deft_optimal_obs),num_of_draws=num_kde_samples,grid=DM_grid,stepsize=DM_stepsize)
DM_deft_draws_obs = DM_deft_obs[0]
DM_deft_obs_distribution  = DM_deft_obs[1]

count_deft_obs = 0
for i in DM_deft_draws_obs: 
    if i < 100: 
        count_deft_obs = count_deft_obs+ 1
print(count_deft_obs)

plt.plot(DM_grid,DM_deft_obs_distribution*1000)
sns.distplot(DM_deft_draws_obs, hist = True, kde = False, rug = True, bins=300,
             color = 'darkblue', 
             kde_kws={'linewidth': 2, 'bw':99},
             rug_kws={'color': 'red'})
plt.xlabel('$DM_{DEFT}$ Observed', fontsize=28)
plt.ylabel('PDF', fontsize=28)
plt.xlim(0,2000)
plt.tight_layout()
plt.savefig('DM_outputs/Counts_below_gap/DEFT_observed.png')
plt.show()

