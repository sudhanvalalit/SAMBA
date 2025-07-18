# Method 3: Multivariate model mixing with a Gaussian process

This method uses the same framework as the previous method, but now includes a Gaussian process (GP) in the mixing.

A diagnostic tool that helps with determining whether or not our mixed model result is reasonable is the Mahalanobis distance, calculated as

$$
D^{2}_{MD} = (\mathbf{y} - \mathbf{m})^{T}\textit{K}^{-1}(\mathbf{y} - \mathbf{m}),
$$

and given in the functions below.

:: samba.gaussprocess
