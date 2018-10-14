#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 03 15:19:50 2017

@author: hamme
"""
import os
import sys
import time
import shutil
import subprocess as sp

files = os.path.join(os.getcwd(),'break.foam')
comms_path = './../transient/comms/'
lock_path = os.path.join(comms_path, 'OpenFOAM.lock')
kill_path = os.path.join(comms_path, 'kill.dat')
fflg = True

while os.path.exists(files) == False:
    if os.path.exists(kill_path) == True:
        sys.exit()
    elif os.path.exists(lock_path) == False:
        in_path = os.path.join(comms_path, 'forces.out')
        if os.path.exists(in_path) == False:
            print('No positions.in. copying...')
            shutil.copyfile('./../fem/positions.in', './comms/positions.in')
        else:
            print('calculating external solver.')
            with open(in_path) as f:
                flg = 0
                points = []
                forces = []
                moments = []
                for i in f:
                    buf = i.strip('\n').split()
                    if len(buf) == 0:
                        continue
                    if buf[0] == 'points':
                        flg = 1
                        continue
                    if buf[0] == 'forces':
                        flg = 2
                        continue
                    if buf[0] == 'moments':
                        flg = 3
                        continue
                    if flg == 1:
                        if len(buf[0])>1 and buf[0][0]=='(':
                            points.append(map(float,[buf[0].strip('('),buf[1],buf[2].strip(')')]))
                    elif flg == 2:
                        if len(buf[0])>1 and buf[0][0]=='(':
                            forces.append(map(float,[buf[0].strip('('),buf[1],buf[2].strip(')')]))
                    elif flg == 3:
                        if len(buf[0])>1 and buf[0][0]=='(':
                            moments.append(map(float,[buf[0].strip('('),buf[1],buf[2].strip(')')]))
                    else:
                        pass

                points = [[0.25, 0.0, 0.0],
                        [0.285, 0.0, 0.0],
                        [0.32, 0.0, 0.0],
                        [0.355, 0.0, 0.0],
                        [0.39, 0.0, 0.0],
                        [0.425, 0.0, 0.0],
                        [0.46, 0.0, 0.0],
                        [0.495, 0.0, 0.0],
                        [0.53, 0.0, 0.0],
                        [0.565, 0.0, 0.0],
                        [0.6, 0.0, 0.0]]

                ccx_inp = os.path.join('./../fem', 'b31.inp') 
                with open(ccx_inp, 'w') as f:
                    f.write('*Node, NSET=NALL\n')
                    for c, i in enumerate(points):
                        f.write(
                                '{0}, {1}, {2}, {3}\n'.format(c+1, i[0], i[1], i[2])
                                )
                    buf = '\n'.join([
                            '*Element, type=B31, ELSET=EALL',
                            ' 1,  1,  2',
                            ' 2,  2,  3',
                            ' 3,  3,  4',
                            ' 4,  4,  5',
                            ' 5,  5,  6',
                            ' 6,  6,  7',
                            ' 7,  7,  8',
                            ' 8,  8,  9',
                            ' 9,  9, 10',
                            '10, 10, 11',
                            '*Beam Section, elset=EALL, material=Material-1, section=RECT',
                            '0.02, 0.02',
                            '0.d0,0.d0,-1.d0',
                            '*Material, name=Material-1',
                            '*Elastic',
                            ' 1.6e+06, 0.4999',
                            '*Boundary',
                            'NALL, 3, 3',
                            'NALL, 4, 4',
                            'NALL, 5, 5',
                            '*Boundary',
                            '1, 1, 6',
                            ])
                    f.write(buf+'\n')

                    dat_path = './../fem/old.dat'
                    if os.path.exists(dat_path) == False:
                        print('No dat file!')
                        pass
                    else:
                        with open(dat_path, 'r') as od:
                            ics = []
                            for c, i in enumerate(od):
                                if c < 3:
                                    pass
                                else:
                                    ics.append(i.strip().split())
                        os.remove('./../fem/old.dat')
                        
                        f.write('*INITIAL CONDITIONS, TYPE=STRESS'+'\n')
                        for i in ics:
                            ics_buf = ','.join([
                                str(i[0]),
                                str(i[1]),
                                str(float(i[2])*1.),
                                str(float(i[3])*1.),
                                str(float(i[4])*1.),
                                str(float(i[5])*1.),
                                str(float(i[6])*1.),
                                str(float(i[7])*1.),
                                ])
                            f.write(ics_buf+'\n')

                    buf = '\n'.join([
                            '*Step',
                            '*Static',
                            '*Cload'
                            ])
                    f.write(buf+'\n')
                    
                    for c, i in enumerate(forces):
                        for cc, j in enumerate(i):
                            if round(j,3) == 0.0:
                                continue
                            elif c+1 ==1:
                                continue
                            f.write(
                                '{0}, {1}, {2}\n'.format(c+1, cc+1, j)
                                )
                    f.write('*Cload\n')
                    
                    for c, i in enumerate(moments):
                        for cc, j in enumerate(i):
                            if round(j,3) == 0.0:
                                continue
                            elif c+1 ==1:
                                continue
                            elif cc+4 == 4:
                                continue
                            elif cc+4 == 5:
                                continue
                            f.write(
                                '{0}, {1}, {2}\n'.format(c+1, cc+4, j)
                                )
                    f.write('*NODE FILE,OUTPUT=2D\nU\n*EL PRINT,ELSET=Eall,FREQUENCY=100\nS\n*END STEP')
 

                ccx_file_path = os.path.join('./../fem', 'b31') 
                cmd = ','.join(['ccx', ccx_file_path, '>', '/dev/null', '2>&1'])
                print(cmd)
                sp.check_call(cmd.split(','))

                ccxf_path = os.path.join('./../fem','b31.frd')
                flg = ''
                with open(ccxf_path, 'r') as cf:
                    temp = []
                    for i in cf:
                        if i[5:9] == 'DISP':
                            flg = '-1'
                        if i[1:3] == '-3':
                            flg = ''
                        if i[1:3] == flg:
                            ttt = [i[11:13],i[13:25],i[25:37],i[37:49]]
                            buf2 = map(float, ttt)
                            temp.append([buf2[1],buf2[2],buf2[3]])
                    temp = temp[0:11]

                for i in range(len(points)):
                    for j in range(3):
                        points[i][j] = points[i][j] + temp[i][j]

                angles = []
                for i in points:
                    angles.append([0.0,0.0,0.0])
    
                # write input           
                out_path = os.path.join(comms_path, 'positions.in')
                with open(out_path, 'w') as o:
                    o.write('points\n')
                    o.write(str(len(points))+'\n')
                    o.write('(\n')
                    for i in points:
                        u1 = i[0]
                        u2 = i[1]
                        u3 = i[2]
                        
                        o.write(
                                '({0:6e} {1:6e} {2:6e})\n'.format(round(u1,6),round(u2,6),round(u3,6))
                                )
                    o.write(');\n')
                    
                    o.write('angles\n')
                    o.write(str(len(points))+'\n')
                    o.write('(\n')
                    for i in angles:
                        o.write(
                                '({0:6e} {1:6e} {2:6e})\n'.format(round(i[0],6),round(i[1],6),round(i[2],6))
                                )
                    o.write(');\n')
                shutil.copyfile('./../fem/b31.dat', './../fem/old.dat')

        # Create Lock File
        with open(lock_path, 'w') as lp:
            pass
        
        #os.remove(lock_path)
        time.sleep(2)
