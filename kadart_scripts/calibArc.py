#!/usr/bin/python

# Script for taking arc calibration frames
# for all Grisms and Slits
# ~/scripts/calibArc.py grism 5 7 11 13 14 15 
# Grism 13 is an echelle, and would require a cross-disperser to replace one of the filters
# ~/scripts/calibArc.py slits pin 05 10 13 18 calcite
# pin = pinhole, calcite? 
# grating side (flat face) facing telescope, prism side (angled face) facing CCD
# measure slit transfer functions
# must to have pinhole!
# for other grisms need order blocker filter! long-pass filters
# test various binning modes
# test various readout rates with bias frames
# determine gain with flats and bias frames

import urllib2
import base64
import json
from math import exp
import time
import sys
import os
import glob
import numpy
from astropy.io import fits
import telOffset

# The names and positions of the grisms/slits in each wheel
grisms = ["empty", "5", "7", "11", "13", 
	"14", "15"]
slits = ["empty", "pin", "05", "10", "13", "18", "calcite"]

# The default window, and a smaller window for testing the counts
# The small window is located away from any nasty CCD features
# It's also relatively near the centre, as filters like
# U and Halpha show significant vignetting
defaultWindow = [0, 2049, 2148, 2048]
defaultWindowSmall = [900, 2849, 200, 200]

# The types of image known to the ARS, and whether
# the shutter should be opened
imageTypes = ["LIGHT", "DARK", "BIAS", "FLAT"]
imageTypesShutterDark = [0, 1, 1, 0]

# The binning options
binModes = ["1x1", "2x2", "3x3", "4x4"]

# Probably not necessary for DFOSC
decayConstants = {"U": 0.0024, "B": 0.0055, "V": 0.0044, "R": 0.0045, "I": 0.0059, "Halpha": 0.0027}
defaultDecayConstant = 0.0040

# Sent a request to the ARS, including login info
def sendRequest(url):
	request = urllib2.Request(url)
	b64str = base64.encodestring("{}:{}".format("dk154", "dk154"))
	request.add_header("Authorization", "Basic {}".format(b64str))
	
	response = urllib2.urlopen(request)
	
	return response

# Call the ARS to do an exposure, specifying the output
# filename based on the object name.
def doExposure(name):
	setObjectName(name)
	url = "http://localhost:8889/api/expose?ccd=CCD3&fe=%25N%2F{}_%2506u.fits".format(name)
	return sendRequest(url)

# Set a parameter in the ARS. By default this is a CCD
# parameter, but it could also be a filter wheel, etc.
def setParam(param, value, device = "CCD3"):
	url = "http://localhost:8889/api/set?async=0&v={}&d={}&n={}".format(value, 
		device, param)
	
	return sendRequest(url)

# Get the full set of parameters for a device
# This is returned in JSON format
def getParams(device = "CCD3"):
	url = "http://localhost:8889/api/get?d={}&e=0".format(device)
	
	return sendRequest(url)

# Parse the JSON data returned by a request to the ARS
def parseJSON(response):
	data = json.loads(response.read())
	return data

# Get the value of a specific parameter
def getParamByName(paramName, device = "CCD3"):
	return parseJSON(getParams(device))["d"][paramName]

# Set the name of the object in the FITS headers
def setObjectName(name):
	return setParam("OBJECT", name)

# Set the positions of the two filter wheels
# filterWheelSetup is a tuple with the filter
# wheel positions for WHL A and WHL B respectively
def setFilterWheel(filterWheelSetup):
	setParam("filter", filterWheelSetup[0], "WASA")
	setParam("filter", filterWheelSetup[1], "WASB")

# Set the CCD window
def setWindow(window):
	windowStr = "{}+{}+{}+{}".format(*window)
	setParam("WINDOW", windowStr)

# Set the CCD window to the default full frame
def setDefaultWindow():
	setWindow(defaultWindow)

# Set the CCD window to a small test frame
def setDefaultWindowSmall():
	setWindow(defaultWindowSmall)

# Set the image type, for the FITS headers
def setImageType(imageType):
	setParam("IMAGETYP", imageType)

# Set whether the shutter should be opened
def setShutterMode(shutterMode):
	setParam("SHUTTER", shutterMode)

# Set the image type to FLAT.
# Also set the shutter to be opened.
def setImageTypeFlat():
	idx = imageTypes.index("FLAT")
	setImageType(idx)
	setShutterMode(imageTypesShutterDark[idx])

# Set the CCD binning to 1x1
def setBinning1x1():
	setParam("binning", 0)

# Set the exposure time of the next frame
def setExpTime(exptime):
	setParam("exposure", "{:.2f}".format(exptime))

# Wait for the exposure to end
# I don't really understand how the CCD
# states work, so this is a bit hacky...
#
# I suggest using "waitForFile", which checks
# whether the CCD has finished reading out the
# latest file to disk, which has proved to
# be reliable
def waitForExposureEnd(estWaitTime = 0.0):
	print("Waiting for camera...")

	time.sleep(estWaitTime + 1.0)

	state = parseJSON(getParams())["state"]

	while state == 2 or state >= 67000000:
		time.sleep(1)
		state = parseJSON(getParams())["state"]
	
#	print("Camera finished")

# Wait until the CCD has finished reading out
# the current frame to file.
def waitForFile(estWaitTime = 0.0):
	print("Waiting for camera...")
	
	# Wait for the expected amount of time
	time.sleep(estWaitTime + 1.0)
	isFileReady = False
	
	while not isFileReady:
		# Get a list of fits files in the most recent
		# image directory, and then sort the files by
		# creation date
		imageDirs = sorted(glob.glob("/data/20*/"))
		latestDir = imageDirs[-1]
		fitsFiles = glob.glob(latestDir + "*.fits")
		creationDates = [os.path.getmtime(file) for file in fitsFiles]
		fitsFilesByDate = zip(*sorted(zip(creationDates, fitsFiles)))[1]
	
		# We are interested in the most recent file
		# A blank file is created as soon as the exposure
		# starts, so we don't need to worry about reading
		# in the previous frame
		file = fitsFilesByDate[-1]
		
		# Calculate how long since the file was last modified
		secsSinceMod = time.time() - os.path.getmtime(file)
	
		# The file is declared as "ready" if:
		# 1. The file is not just an empty header (~8kb)
		# 2. The file has not been modified in the last second
		# If 1 is not satisfied, readout has not yet begun
		# If 2 is not satisfied, the image is actively being
		# written to disk
		if os.stat(file).st_size > 8640 and secsSinceMod > 1.:
			isFileReady = True
		# Wait a little bit, to prevent thrashing the disk
		else:
			time.sleep(2.0)

	print(file)
	return file

# Calculate the median counts in the file
# The mean has a habit of being biased by the
# unexposed regions
# Also, for test frames, the bottom left corner
# pixel tends to have very high (10**9!) counts,
# which is obviously bad for a mean
def calcImageMedian(file):
	f = fits.open(file)
	image = f[0].data
	median = numpy.median(image)
	f.close()
	return median
	
# The ARS calculates the average counts on each
# frame.
# However, the mean has been found to be misleading
# at times - use calcImageMedian instead
def getAverageCounts():
	return getParamByName("average")	

# Estimate the exposure time of the next frame
# This takes into account:
#   1. The counts in the previous frame
#   2. The constant bias level
#   3. The decay (or growth) of sky brightness with time
def estimateNextExpTime(targetCounts, biasLevel, expTime, readoutTime, decayConst, filename):

	# Time since the start of the last frame
	totTime = expTime + readoutTime

	avgCounts = calcImageMedian(filename)

	# If the counts are very high, we are likely
	# overexposed, or at least non-linear.
	# Therefore, any time calculation will
	# be incorrect. Simply assume the next
	# time is zero.
	# If evening, this will cause the script to
	# wait longer. If morning, the sky is 
	# already too bright.
	if avgCounts > 700000.:
		print("Counts over 700000")
		return -1.0

	# Calculate how long the last frame should have 
	# been to get the ideal counts, and then apply
	# the decay (growth) model to estimate the
	# time of the next frame.
	countsPerSec = (avgCounts - biasLevel) / expTime

	idealTimeLastFrame = (targetCounts-biasLevel) / countsPerSec

	estTimeNextFrame = exp(decayConst * totTime) * idealTimeLastFrame
	
	print("Last frame {:.2f}s, {:.0f} counts, target {:.0f} counts.".format(expTime, avgCounts, targetCounts))
	print("Ideal time for last frame: {:.2f}s".format(idealTimeLastFrame))
	print("Estimate time next frame:  {:.2f}s".format(estTimeNextFrame))
	
	return estTimeNextFrame

# Parse a list of filter names.
# These are matched to the known list of filter names
# in the two filter wheels.
# The returned value are the indices to set the two
# filter wheels correctly (WHL A must be empty if
# using something in WHL B!)
def parseFilters(filterList):
	filterWheelSetups = []

	for filterName in filterList:
		
		if filterName in grisms:
			idx = grisms.index(filterName)
			entry = [idx, 0]
		elif filterName in slits:
			idx = slits.index(filterName)
			entry = [0, idx]
		else:
			raise ValueError("Unknown filter {}".format(filterName))
	
		filterWheelSetups.append(entry)

	return filterWheelSetups

# Take a test exposure using a small window,
# to check the sky counts.
def doTestFlat(expTime = 0.2):
	setDefaultWindowSmall()
	setImageTypeFlat()
	setBinning1x1()
	setExpTime(expTime)
	doExposure("test")
	
	filename = waitForFile(expTime + 1.0)
	return filename

# The main flat taking function.
# Matches the filter and sets the filter wheels
# Determines the decay (growth) model to use
# Waits for the counts to be in the acceptable range
#    (or quits if it is too late already)
# Then takes a series of flats, adjusting the exposure
# time after each one, unless it is now too late
def takeFlatsForFilter(filterName, isMorning, minExpTime = 0.4, 
	maxExpTime = 30.0, nFlats = 8, targetCounts = 300000, 
	biasLevel = 10000, readoutTime = 23.8):

	print("Taking {} flat fields in {}".format(nFlats, filterName))

	# Determine the filter, setup the wheels,
	# and set the decay (growth) model	
	filterWheelSetup = parseFilters([filterName])[0]
	setFilterWheel(filterWheelSetup)
	
	if filterName in decayConstants.keys():
		decayConst = decayConstants[filterName]
		print("Decay constant for filter {}: {}".format(filterName, decayConst))
	else:
		decayConst = defaultDecayConstant
		print("Decay constant for filter {} set to default: {}".format(filterName, decayConst))
	
	if isMorning:
		decayConst = -decayConst
	
	# Do test exposures until counts are ok,
	# or instead we determine it is too late
	# to take flats in this filter.

	if isMorning:
		testExpTime = 1.0
	else:
		testExpTime = 0.4
	isTimeOutOfBounds = False
	keepChecking = True
	
	while keepChecking:
		print("Taking test image")
		
		filename = doTestFlat(testExpTime)
	
		estTimeNextFrame = estimateNextExpTime(targetCounts, biasLevel, 
			testExpTime, readoutTime, decayConst, filename)

		# If the exp time is below the minimum,
		# and the sky is getting brighter, too late.		
		if isMorning and estTimeNextFrame < minExpTime:
			isTimeOutOfBounds = True
			print("Exposure time is already too short, skipping {} filter".format(filterName))
			break
		# Similarly, if too dark and getting darker,
		# too late.
		elif not isMorning and estTimeNextFrame > maxExpTime:
			isTimeOutOfBounds = True
			print("Exposure time is already too long, skipping {} filter".format(filterName))
			break
		
		# If the exp time is OK, time to start taking flats
		if minExpTime <= estTimeNextFrame <= maxExpTime:
			keepChecking = False
			print("Start taking {} flats".format(filterName))
			break
		# If not ok, but not too late, we need to wait
		else:
			print("Waiting before taking {} flats".format(filterName))
			
		
		# This is only reached if still waiting for the sky
		# brightness. Wait for a little while.
		# Use 30s to avoid spamming small test images
		# (30s is equivalent to only a single full frame)
		# The estimated time is negative if the frame was utterly
		# overexposed, so wait even longer to avoid spam when the
		# sky is clearly way too bright
		if estTimeNextFrame < 0.0:
			print("Last frame was overexposed, waiting 2 minutes")
			time.sleep(120)
		else:
			time.sleep(30)

	# It is too late for these flats
	if isTimeOutOfBounds:
		return
	
	# Set up for full frame flats
	setImageTypeFlat()
	setBinning1x1()
	setDefaultWindow()
	nFramesTaken = 0

	if isMorning:
		timeStr = "Morning"
	else:
		timeStr = "Evening"
	
	# Keep goung until enough flats are taken
	while nFramesTaken < nFlats:
		setExpTime(estTimeNextFrame)

		# Offset telescope and wait a second
		telOffset.do_iterative_offsets(nFramesTaken)
		time.sleep(1)

		doExposure("SkyFlat_{}_{}".format(filterName, timeStr))

		filename = waitForFile(estTimeNextFrame + readoutTime)
		nFramesTaken += 1
		
		print("Flat {} taken".format(nFramesTaken))

		# Calculate the time for the next frame
		estTimeNextFrame = estimateNextExpTime(targetCounts, biasLevel, 
			estTimeNextFrame, readoutTime, decayConst, filename)
		
		# If it's now too late to keep taking flats
		# in this filter, stop doing so	
		if isMorning and estTimeNextFrame < minExpTime:
			print("Next exposure time is too short".format(filterName))
			break
		elif not isMorning and estTimeNextFrame > maxExpTime:
			print("Next exposure time is too long".format(filterName))
			break
	
	print("Completed taking {} flats".format(filterName))
	# Reset telescope offset
	telOffset.do_iterative_offsets(0)

# Take flats for each filter in sequence
def takeFlats(filterNames, isMorning, nFlats = 8):
	for filterName in filterNames:
		takeFlatsForFilter(filterName, isMorning, nFlats = nFlats)

# Parse the arguments
# It is expected that each arguments is
# either "morning" or "evening", or
# a filter name.
# The validity of filter names is checked later
# (and will result in a ValueError)
if __name__ == "__main__":

	if "takeFlats.py" in sys.argv[0]:
		args = sys.argv[1:]
	else:	
		args = sys.argv

	if len(args) == 0:
		print("\n")
		print("DFOSC flat script")
		print(" ")
		print("Usage:")
		print("takeFlats.py [morning|evening] [?nframes] [filter1] [filter2] ...")
		print("e.g. takeFlats.py evening 8 Halpha V R")
		print("Flats will be taken in the order specified")
		print("nframes is an optional argument.")
		print(" ")
		print("By default 8 flats are taken. If a larger number")
		print("is specified, it is possible that it will get too")
		print("dark or too bright if several filters are specified")
		print(" ")
		print("This script now automatically dithers between frames!")
		print(" ")
		print("For the filters most often used, the commands are:")
		print("~/scripts/takeFlats.py evening Halpha U B V R I")
		print("~/scripts/takeFlats.py morning I R V B U Halpha")
		print()
		sys.exit()

	filterNames = []
	nFrames = 8

	for arg in args:
		argLowercase = arg.lower()
		
		try:
			argAsInt = int(arg)
		except:
			argAsInt = None
		
		if argLowercase == "morning":
			isMorning = True
			print("Morning")
		elif argLowercase == "evening":
			isMorning = False
			print("Evening")
		elif arg in grisms or arg in slits:
			filterNames.append(arg)
		elif argAsInt is not None:
			nFrames = argAsInt
		else:
			raise ValueError("Unknown argument or filter: '%s'" % (arg))

	if len(filterNames) == 0:
		raise ValueError("No filters specified")

	s = "Taking {} flats in filters: ".format(nFrames)
	for filterName in filterNames:
		s += "{} ".format(filterName)
	print(s)
	
	takeFlats(filterNames, isMorning, nFrames)

	print("\n\nFinished taking flat fields!\n")
