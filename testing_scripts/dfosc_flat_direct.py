from argparse import ArgumentParser
import telnetlib
import time
from dk154_control.camera.ccd3 import Ccd3
from dk154_control.tcs.ascol import Ascol

#Directly connect to dfosc and send commands via telnet terminal
host = '192.168.132.58'
port = 4001

def take_flats_grism3(nframes, slit, filt):
    # connect to the DFOSC
    with telnetlib.Telnet(host, port) as tn:
        # move to the correct positions
        tn.write(b'G2\n')
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'A{slit}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'F{filt}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        time.sleep(15)

        tn.write(f'AM+450\n'.encode())      #better slit alignment

        with Ascol() as ascol:
        # take the flats
            for i in range(nframes):
                exp_time = 20   # TODO this value depends on the grism, and time of twilight... Calculate from latest/test image?
                ccd3 = Ccd3()
                exp_params = {}
                exp_params['CCD3.exposure'] = str(exp_time)
                exp_params['CCD3.IMAGETYP'] = 'FLAT,SKY'
                exp_params['CCD3.OBJECT'] = 'FLAT1'
                exp_params['WASA.filter'] = '0'
                exp_params['WASB.filter'] = '0'
                ccd3.set_exposure_parameters(params=exp_params)
                ascol.shop('0')
                ccd3.start_exposure(f'test_flat_G3_A{slit}_{i}.fits')
                time.sleep(exp_time+30)

        # return wheels to position 1
        tn.write(b'G1\n')
        tn.write(b'A1\n')
        tn.write(b'F1\n')

    return

def take_flats_grism5(nframes, slit, filt):
    # connect to the DFOSC
    with telnetlib.Telnet(host, port) as tn:
        # move to the correct positions
        tn.write(b'G3\n')
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'A{slit}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'F{filt}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        time.sleep(20)

        tn.write(f'AM+450\n'.encode())      #better slit alignment

        with Ascol() as ascol:
        # take the flats
            for i in range(nframes):
                exp_time = 20   # TODO this value depends on the grism, and time of twilight... Calculate from latest/test image?
                ccd3 = Ccd3()
                exp_params = {}
                exp_params['CCD3.exposure'] = str(exp_time)
                exp_params['CCD3.IMAGETYP'] = 'FLAT,SKY'
                exp_params['CCD3.OBJECT'] = 'FLAT1'
                exp_params['WASA.filter'] = '0'
                exp_params['WASB.filter'] = '0'
                ccd3.set_exposure_parameters(params=exp_params)
                ascol.shop('0')
                ccd3.start_exposure(f'test_flat_G5_A{slit}_{i}.fits')
                time.sleep(exp_time+30)

        tn.write(b'G1\n')
        tn.write(b'A1\n')
        tn.write(b'F1\n')

    return

def take_flats_grism6(nframes, slit, filt):
    # connect to the DFOSC
    with telnetlib.Telnet(host, port) as tn:
        # move to the correct positions
        tn.write(b'G4\n')
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'A{slit}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'F{filt}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        time.sleep(25)

        tn.write(f'AM+450\n'.encode())      #better slit alignment

        with Ascol() as ascol:
        # take the flats
            for i in range(nframes):
                exp_time = 20   # TODO this value depends on the grism, and time of twilight... Calculate from latest/test image?
                ccd3 = Ccd3()
                exp_params = {}
                exp_params['CCD3.exposure'] = str(exp_time)
                exp_params['CCD3.IMAGETYP'] = 'FLAT,SKY'
                exp_params['CCD3.OBJECT'] = 'FLAT1'
                exp_params['WASA.filter'] = '0'
                exp_params['WASB.filter'] = '0'
                ccd3.set_exposure_parameters(params=exp_params)
                ascol.shop('0')
                ccd3.start_exposure(f'test_flat_G6_A{slit}_{i}.fits')
                time.sleep(exp_time+30)

        tn.write(b'G1\n')
        tn.write(b'A1\n')
        tn.write(b'F1\n')

    return

def take_flats_grism7(nframes, slit, filt):
    # connect to the DFOSC
    with telnetlib.Telnet(host, port) as tn:
        # move to the correct positions
        tn.write(b'G5\n')
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'A{slit}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'F{filt}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        time.sleep(25)
        
        tn.write(f'AM+450\n'.encode())      #better slit alignment

        with Ascol() as ascol:
        # take the flats
            for i in range(nframes):
                exp_time = 20   # TODO this value depends on the grism, and time of twilight... Calculate from latest/test image?
                ccd3 = Ccd3()
                exp_params = {}
                exp_params['CCD3.exposure'] = str(exp_time)
                exp_params['CCD3.IMAGETYP'] = 'FLAT,SKY'
                exp_params['CCD3.OBJECT'] = 'FLAT1'
                exp_params['WASA.filter'] = '0'
                exp_params['WASB.filter'] = '0'
                ccd3.set_exposure_parameters(params=exp_params)
                ascol.shop('0')
                ccd3.start_exposure(f'test_flat_G7_A{slit}_{i}.fits')
                time.sleep(exp_time+30)

        tn.write(b'G1\n')
        tn.write(b'A1\n')
        tn.write(b'F1\n')

    return

def take_flats_grism8(nframes, slit, filt):
    # connect to the DFOSC
    with telnetlib.Telnet(host, port) as tn:
        # move to the correct positions
        tn.write(b'G6\n')
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'A{slit}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'F{filt}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        time.sleep(20)

        tn.write(f'AM+450\n'.encode())      #better slit alignment

        with Ascol() as ascol:
        # take the flats
            for i in range(nframes):
                exp_time = 20   # TODO this value depends on the grism, and time of twilight... Calculate from latest/test image?
                ccd3 = Ccd3()
                exp_params = {}
                exp_params['CCD3.exposure'] = str(exp_time)
                exp_params['CCD3.IMAGETYP'] = 'FLAT,SKY'
                exp_params['CCD3.OBJECT'] = 'FLAT1'
                exp_params['WASA.filter'] = '0'
                exp_params['WASB.filter'] = '0'
                ccd3.set_exposure_parameters(params=exp_params)
                ascol.shop('0')
                ccd3.start_exposure(f'test_flat_G8_A{slit}_{i}.fits')
                time.sleep(exp_time+30)

        tn.write(b'G1\n')
        tn.write(b'A1\n')
        tn.write(b'F1\n')

    return

def take_flats_grism14(nframes, slit, filt):
    # connect to the DFOSC
    with telnetlib.Telnet(host, port) as tn:
        # move to the correct positions
        tn.write(b'G7\n')
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'A{slit}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        tn.write(f'F{filt}\n'.encode())
        print(tn.read_until(b'\n').decode('utf-8'))
        time.sleep(20)

        tn.write(f'AM+450\n'.encode())      #better slit alignment

        with Ascol() as ascol:
        # take the flats
            for i in range(nframes):
                exp_time = 20   # TODO this value depends on the grism, and time of twilight... Calculate from latest/test image?
                ccd3 = Ccd3()
                exp_params = {}
                exp_params['CCD3.exposure'] = str(exp_time)
                exp_params['CCD3.IMAGETYP'] = 'FLAT,SKY'
                exp_params['CCD3.OBJECT'] = 'FLAT1'
                exp_params['WASA.filter'] = '0'
                exp_params['WASB.filter'] = '0'
                ccd3.set_exposure_parameters(params=exp_params)
                ascol.shop('0')
                ccd3.start_exposure(f'test_flat_G14_A{slit}_{i}.fits')
                time.sleep(exp_time+30)

        tn.write(b'G1\n')
        tn.write(b'A1\n')
        tn.write(b'F1\n')

    return  

def take_flats_grism15(nframes,slit,filt):
    # connect to the DFOSC
    with telnetlib.Telnet(host, port) as tn:
        # move to the correct positions
        tn.write(b'G8\n')
        tn.write(f'A{slit}\n'.encode())
        tn.write(f'F{filt}\n'.encode())
        time.sleep(15)

        tn.write(f'AM+450\n'.encode())      #better slit alignment

        with Ascol() as ascol:
        # take the flats
            for i in range(nframes):
                exp_time = 20   # TODO this value depends on the grism, and time of twilight... Calculate from latest/test image?
                ccd3 = Ccd3()
                exp_params = {}
                exp_params['CCD3.exposure'] = str(exp_time)
                exp_params['CCD3.IMAGETYP'] = 'FLAT,SKY'
                exp_params['CCD3.OBJECT'] = 'FLAT1'
                exp_params['WASA.filter'] = '0'
                exp_params['WASB.filter'] = '0'
                ccd3.set_exposure_parameters(params=exp_params)
                ascol.shop('0')
                ccd3.start_exposure(f'test_flat_G15_A{slit}_{i}.fits')
                time.sleep(exp_time+30)

        tn.write(b'G1\n')
        tn.write(b'A1\n')
        tn.write(b'F1\n')

    return

def take_flat_empty(nframes,slit,filt):
    # connect to the DFOSC
    with telnetlib.Telnet(host, port) as tn:
        # move to the correct positions
        tn.write(b'G1\n')
        tn.write(f'A{slit}\n'.encode())
        tn.write(f'F{filt}\n'.encode())
        time.sleep(15)
        tn.write(f'AM+450\n'.encode())      #better slit alignment

        with Ascol() as ascol:
        # take the flats
            for i in range(nframes):
                exp_time = 20   # TODO this value depends on the grism, and time of twilight... Calculate from latest/test image?
                ccd3 = Ccd3()
                exp_params = {}
                exp_params['CCD3.exposure'] = str(exp_time)
                exp_params['CCD3.IMAGETYP'] = 'FLAT,SKY'
                exp_params['CCD3.OBJECT'] = 'FLAT1'
                exp_params['WASA.filter'] = '0'
                exp_params['WASB.filter'] = '0'
                ccd3.set_exposure_parameters(params=exp_params)
                ascol.shop('0')
                ccd3.start_exposure(f'test_flat_A{slit}_{i}.fits')
                time.sleep(30)

        tn.write(b'G1\n')
        tn.write(b'A1\n')
        tn.write(b'F1\n')

    return


if __name__ == '__main__':
    # define the parser
    parser = ArgumentParser(description='Take flat calibration images with DFOSC')
    parser.add_argument('--nframes', help='Number of frames to take', type=int)
    parser.add_argument('--grism', help='Grism position, 1-8', type=int)
    parser.add_argument('--slit' ,nargs = '+',help='Slit position to use, 1-8, single slit position')
    parser.add_argument('--filt',help='Filter position to use, 1-8, single filter position')
    args = parser.parse_args()
    
    if args.grism == 2:
        take_flats_grism3(args.nframes, args.slit, args.filt)
    elif args.grism == 3:
        take_flats_grism5(args.nframes, args.slit, args.filt)
    elif args.grism == 4:
        take_flats_grism6(args.nframes, args.slit, args.filt)
    elif args.grism == 5:
        take_flats_grism7(args.nframes, args.slit, args.filt)
    elif args.grism == 6:
        take_flats_grism8(args.nframes, args.slit, args.filt)
    elif args.grism == 7:
        take_flats_grism14(args.nframes, args.slit, args.filt)
    elif args.grism == 8:
        take_flats_grism15(args.nframes, args.slit, args.filt)
    elif args.grism == 1:
        take_flat_empty(args.nframes, args.slit, args.filt)       
    else:
        print('Grism position out of range, must be 1-8')
