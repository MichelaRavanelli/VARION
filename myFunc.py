import numpy as np
########################################################
## FUNCTIONS ##  
def no_outlayer_mask(vector):
    mask = (np.abs(vector) < 0.02)
    return mask
##
def integrate(vector,dx):
    '''
    This function applies the Trapezoidal Rule in order to compute an integral.
    input:
        - array with the samples of the function
        - dx
    output:
        - array with the cumulate of the input array
    '''
    aree = np.zeros(len(vector)-1)
    for i in xrange(0,len(aree)):
        aree[i] = ((vector[i]+vector[i+1])*dx)/2.0      
    cum = np.zeros(len(aree))
    cum[0] = aree[0]
    for i in xrange(1,len(cum)):
        cum[i] = cum[i-1] + (aree[i])          
    return cum
##   
def coord_geog(x,y,z):
	'''
	input: x,y,z
	output: Latitude (F) and Longitude (L) WGS84
	'''
	# Longitudine calcolabile senza iterazioni
	L = np.arctan2(y,x)
	r = (x**2 + y**2)**0.5
	# parametri WGS84
	a = 6378137
	f = 1/298.257223563
	b = a*(1-f)
	e = (1-(b**2)/(a**2))**0.5
	# I step
	# ip h=0
	F  = np.arctan2(z, r*(1-e**2))
	Rn = a/((1-(e**2)*(np.sin(F))**2))**0.5
	# Proviamo 50 iterazioni
	for i in xrange(0,50):
  		        h  = r/np.cos(F) - Rn
  		        F  = np.arctan2((z*(Rn+h)),(r*Rn*(1-e**2)+h))
  		        Rn = a/((1-(e**2)*(np.sin(F))**2))**0.5  		
	L_grad = L/(np.pi)*180
	F_grad = F/(np.pi)*180			
	return F_grad, L_grad
########################################################