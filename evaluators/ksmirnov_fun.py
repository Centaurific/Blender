import pickle, os, sys, string
os.chdir(os.getenv('HOME') + '/Documents/Blender')
import numpy as np 
from numpy import matlib 
from scipy import stats
import pandas as pd
from gensim import utils
from sklearn import feature_extraction
from statsmodels.distributions import empirical_distribution as ed 
from utils import text_fun


def ks(cdfVec1, cdfVec2):
    """ Computes the Kolmogorov-Smirnov Distance between 2 cdf vectors."""
    return(max(abs(cdfVec1 - cdfVec2)))

def cdf(array, grid_pts = 500):
    """This takes a 2D array (matrix) of jaccard indices and returns the cdf values on a grid with grid_pts points equally spaced from 0 to 1.
    """
    array = np.array(array)
    utVec = np.diagonal(array)
    for i in range(1, array.shape[0]):
        utVec = np.concatenate([utVec, np.diagonal(array, i)])
    xgrid = np.linspace(0, 1, grid_pts)
    ecdf = ed.ECDF(utVec)
    yvals = ecdf(xgrid)
    return(yvals)

def ksFunctionGenerator(textList, grid_pts = 500):
	""" Takes a list of lists as an argument, where each sub-list has tokens.  It returns a new function that evaluates the Kolmogorov-Smirnov distance of a new idea from the baseline CDF generated by textList."""
	for i, text in enumerate(textList):
		textList[i] = ' '.join(text)

	# initializes a counter from sklearn
	vectorizer = feature_extraction.text.CountVectorizer() 
	dtm = vectorizer.fit_transform(textList) 
	dtm = dtm.toarray()
	vocab = vectorizer.get_feature_names() # get all the words
	dtm = pd.DataFrame(dtm, columns = vocab) 
	tdm = dtm.transpose() # term-doc mat = transpose of doc-term mat
	idx = tdm.sum(axis = 1).sort_values(ascending = False).index 
	tdm = tdm.ix[idx] # sort the term-doc mat by word frequency
	totals = tdm.sum(axis = 1)
	wordFreqThreshold = 10
	tdm = tdm[totals > wordFreqThreshold] # remove rows for infrequent words
	totals = totals[totals > wordFreqThreshold]
	tdmInd = tdm > 0
	tdmInd = tdmInd.astype(int)

	interMat = pd.DataFrame.dot(tdmInd, tdmInd.transpose())

	# Union(A, B) = A + B - Intersection(A, B)
	totalsMat = matlib.repmat(np.diagonal(interMat), interMat.shape[0], 1)
	unionMat = totalsMat + np.transpose(totalsMat) - interMat
	vocab = list(interMat.index)

	# Need to remove words in the original lists
	for i, doc in enumerate(textList):
		temp = utils.simple_preprocess(doc)
		temp = list(set(temp) & set(vocab))
		temp.sort()
		textList[i] = temp

	# removes empty documents
	textList = [doc for doc in textList if doc]
	nums = [i for i in range(0, len(vocab))]
	wordToNum = dict(zip(vocab, nums))
	numToWord = dict(zip(nums, vocab))
	jaccardMat = pd.DataFrame(interMat / unionMat, index = vocab, 
		columns = vocab)

	def jaccard(text):
		index = [wordToNum[word] for word in text if \
			word in wordToNum.keys()]
		out = jaccardMat.iloc[index, index]
		return(out)

	cdfMat = np.zeros([grid_pts, len(textList)])
	for i, doc in enumerate(textList):
			cdfMat[:, i] = cdf(jaccard(doc), grid_pts)

	baselineCDF = cdfMat.sum(1) / len(textList)
		
	def ksEvaluator(tokenList, verbose = None):
		if verbose:
			jaccard_mat = jaccard(tokenList)
			print('Jaccard matrix computed')
			cdf_vec = cdf(jaccard_mat, grid_pts)
			print('CDF vector created')
			return ks(cdf_vec, baselineCDF)
		else:
			return ks(cdf(jaccard(tokenList), grid_pts), 
				baselineCDF)
			
	return ksEvaluator



