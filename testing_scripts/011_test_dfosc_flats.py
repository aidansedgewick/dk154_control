# script for taking n number of flats for various slit, grism, and filter combinations with DFOSC
# useage: dfosc_flats.py [nframes] [grism] [slit] [filter]
# grism slit and filter are given either as either one number or multiple numbers separated by commas
# example: dfosc_flats.py 4 3,5,6,8,14,15 1,1.5,2,2.5 0

# import necessary packages
import dk154_control.dfosc.dfosc as df
from argparse import ArgumentParser
from logging import getLogger
import time
from dk154_control.camera.ccd3 import Ccd3
from dk154_control.tcs.ascol import Ascol
import yaml

dfosc_setup = yaml.load(open('dk154_control/dfosc/dfosc_setup.yaml'), Loader=yaml.FullLoader)

#TODO - Write correct header information to the FITS files, and exposure times

def take_flats(nframes, grism, slit, filter):

	exp_time = 5  # TODO this value depends on the grism, and time of twilight... Calculate from latest/test image??
	exp_type = 'FLAT,SKY'
	obj_name = 'FLAT1'
	filter_pos = dfosc_setup['filter'][filter]
	grism_pos = dfosc_setup['grism'][grism]
	slit_pos = dfosc_setup['slit'][slit]
	nframes = nframes

	# connect to the DFOSC
	with df.Dfosc() as spec:

		spec.gg(grisms[str(grism_pos)])
		spec.ag(slits[str(slit_pos)])
		spec.fg(filters[str(filter_pos)])
		time.sleep(15)

		"""if spec.g() == 'y' and spec.a() == 'y' and spec.f() == 'y':
			print('All wheels are in position')
		else:
			print('Wheels are not in position, waiting 10 seconds')
			time.sleep(10)
			return"""  #TODO: this if statement is not working properly, fix at somepoint
		
		# read the positions
		ap_pos = spec.ap()
		gr_pos = spec.gp()
		fr_pos = spec.fp()
		# print the positions
		print(f'Aperture position: {ap_pos}')
		print(f'Grism position: {gr_pos}')
		print(f'Filter position: {fr_pos}')

	# take the flats
	with Ascol() as ascol:
		ccd3 = Ccd3()

		# set the exposure parameters
		exp_params = {}
		exp_params['CCD3.exposure'] = str(exp_time)
		exp_params['CCD3.IMAGETYP'] = str(exp_type)
		exp_params['CCD3.OBJECT'] = str(obj_name)
		exp_params['WASA.filter'] = "0"
		exp_params['WASB.filter'] = "0"
		
		ccd3.set_exposure_parameters(params=exp_params)
		
		ascol.shop('0')
		ccd3.set_exposure_parameters(params=exp_params)
		ccd3.start_exposure()
		time.sleep(exp_time + 30)

	
if __name__ == '__main__':
	# define the parser
	parser = ArgumentParser(description='Take calibration flats with DFOSC, see dfosc_setup.json for expected grism, slit, and filter positions')
	parser.add_argument('-n', type=int, help='Number of frames to take')
	parser.add_argument('-g', type=str, choices= dfosc_setup['grism'].keys() ) 
	parser.add_argument('-s', type=str, choices= dfosc_setup['slit'].keys() ) 
	parser.add_argument('-f', type=str, choices= dfosc_setup['filter'].keys() )
	#TODO: update filter list when filters are added
	args = parser.parse_args()
	
	frames = args.n
	grisms = args.g
	slits = args.s
	filters = args.f

	for grism in grisms:
		for slit in slits:
			for filter in filters:
				take_flats(frames, grism, slit, filter)
				print(f'{frames} flats taken for grism {grism}, slit {slit}, filter {filter}')

	print('All flats taken')

