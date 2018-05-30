#!/usr/bin/env python

'''
unwrap convert SIEMENS physio MR dicom. re-implement https://github.com/CMRR-C2P/MB extractCMRRPhysio.m in pyton

Author: YingLi Lu
Email:  yinglilu@gmail.com
Date:   2018-05-24

note:
    Tested on ubuntu 16.04, python 2.7.14
'''

import os
import sys
import logging
import struct

import pydicom

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s -%(message)s')


def extract_cmrr_physio(filename, output_path):
    '''
    Extract physiological log files from encoded "_PHYSIO" DICOM file
    generated by CMRR MB sequences ( >= R015, >= VD13A)
        E. Auerbach, CMRR, 2016

    Inputs:
        filename = 'XXX.dcm'
        output_path = '/path/to/output/'

    Usage:
        extract_cmrr_physio(dicom_filename, output_path);

    note:
        write *.log files to output_path

    This function expects to find a single encoded "_PHYSIO" DICOM file
    generated by the CMRR C2P sequences >= R015. It will extract and write
    individual log files(*_ECG.log, *_RESP.log, *_PULS.log, *_EXT.log,
    *_Info.log) compatible with the CMRR C2P sequences >= R013. Only log
    files with nonzero traces will be written.

    '''

    try:
        dataset = pydicom.read_file(filename, stop_before_pixels=True)

        image_type = dataset.ImageType
        private_7fe1_0010_value = str(dataset[(0x7fe1, 0x0010)].value)

        if image_type == ['ORIGINAL', 'PRIMARY', 'RAWDATA', 'PHYSIO'] and \
                private_7fe1_0010_value.strip() == 'SIEMENS CSA NON-IMAGE':

            private_7fe1_1010_value = dataset[(0x7fe1, 0x1010)].value
            np = len(private_7fe1_1010_value)
            rows = int(dataset.AcquisitionNumber)
            columns = np/rows
            numFiles = columns/1024

            if np % rows != 0 or columns % 1024 != 0:
                logging.error(
                    'Invalid image size ({} x{})!'.format(columns, rows))
                return

            parts = [private_7fe1_1010_value[i:i+np/numFiles]
                     for i in range(0, np, np/numFiles)]

            endian = sys.byteorder
            for part in parts:

                if endian == 'little':
                    datalen = struct.unpack('<I', part[0:4])[0]
                    filenamelen = struct.unpack('<I', part[4:8])[0]
                else:
                    datalen = struct.unpack('>I', part[0:4])[0]
                    filenamelen = struct.unpack('>I', part[4:8])[0]

                log_filename = part[8:8+filenamelen]
                log_data = part[1024:1024+datalen]

                # write log file
                full_log_filename = os.path.join(output_path, log_filename)
                #logging.info('writing {}'.format(full_log_filename))
                with open(full_log_filename, 'w') as f:
                    f.write(log_data)

    except Exception as e:
        logging.exception(e)
        return


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Usage: python extract_cmrr_physio.py dicom_filename output_path'
        sys.exit(1)

    filename = sys.argv[1]
    output_path = sys.argv[2]

    extract_cmrr_physio(filename, output_path)