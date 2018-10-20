#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 03 15:19:50 2017

@author: mmer547
"""
import os
import sys
import time
import shutil
import subprocess as sp

# 初期化
files = os.path.join(os.getcwd(),'break.foam')
# OpenFOAMのコミュニケ―ションディレクトリのパス
comms_path = './../transient/comms/'
# lumpedPointのlockファイルのパス
lock_path = os.path.join(comms_path, 'OpenFOAM.lock')
# 計算を終了するときの
kill_path = os.path.join(comms_path, 'kill.dat')
# FEMのインプットになるforces.out
in_path = os.path.join(comms_path, 'forces.out')
# Culculixのインプットパス
ccx_inp = os.path.join('./../fem', 'b31.inp')
# LumpedPoint用のインプットファイルパス
out_path = os.path.join(comms_path, 'positions.in')
# 2ステップ以降の計算でリスタート計算をするときのフラグ
resflg = False
# ひとつ前の計算ステップでの時
oldtimes = 0.0
# FEMのAMPRITUDEの名前に付ける数字
ampnum = 0
# 要素の節点数
num_node = 41
# beamのX座標最小値
x_min = 0.25
# beamのX座標最大値
x_max = 0.6

#ここからループ
while os.path.exists(files) == False:
    # kill.datが生成されると終了
    if os.path.exists(kill_path) == True:
        sys.exit()
    # lockファイルがない場合
    elif os.path.exists(lock_path) == False:
        # 初期状態ではforces.outがないためpositions.inをコピーする
        if os.path.exists(in_path) == False:
            # print('No positions.in. copying...')
            # shutil.copyfile('./../fem/positions.in', './comms/positions.in')
            pass
        else:
            print('calculating external solver.')
            # forces.outの中身を読み込む
            with open(in_path) as f:
                flg = 0
                points = []
                forces = []
                moments = []
                for i in f:
                    buf = i.strip('\n').split()
                    # 空白行は読み飛ばし
                    if len(buf) == 0:
                        continue
                    # 次巻を読み取る行が来た場合
                    if buf[0] == '//':
                        times = float(buf[3].split('=')[1])
                        continue
                    # 節点座標を読み取る行が来た場合
                    # if buf[0] == 'points':
                    #     flg = 1
                    #     continue
                    # 力を読み取る行が来た場合
                    if buf[0] == 'forces':
                        flg = 2
                        continue
                    # モーメントを読み取る行が来た場合
                    if buf[0] == 'moments':
                        flg = 3
                        continue

                    # フラグに合わせて処理を実施(今のところ差がないです)
                    # if flg == 1:
                    #     if len(buf[0])>1 and buf[0][0]=='(':
                    #         points.append(map(float,[buf[0].strip('('),buf[1],buf[2].strip(')')]))
                    # elif flg == 2:
                    if flg == 2:
                        if len(buf[0])>1 and buf[0][0]=='(':
                            forces.append(map(float,[buf[0].strip('('),buf[1],buf[2].strip(')')]))
                    elif flg == 3:
                        if len(buf[0])>1 and buf[0][0]=='(':
                            moments.append(map(float,[buf[0].strip('('),buf[1],buf[2].strip(')')]))
                    else:
                        pass

                # 初期のpointsの作成
                points = []
                for i in range(num_node):
                    points.append([(x_max-x_min)/(num_node-1)*i+x_min, 0.0, 0.0])

                # FEMインプットの書きだし
                with open(ccx_inp, 'w') as f:
                    # 最初のステップの場合
                    if resflg == False:
                        # 節点の書き出し
                        f.write('*Node, NSET=NALL\n')
                        for c, i in enumerate(points):
                            f.write(
                                    '{0}, {1}, {2}, {3}\n'.format(c+1, i[0], i[1], i[2])
                                    )

                        buf = '*Element, type=B31, ELSET=EALL\n'
                        for i in range(num_node-1):
                            buf += '{0}, {1}, {2}'.format(i+1,i+1,i+2)
                            buf += '\n'
                        # 断面プロパティの書き出し
                        buf += '\n'.join([
                                '*Beam Section, elset=EALL, material=Material-1, section=RECT',
                                '0.02, 0.02',
                                '0.d0,0.d0,-1.d0'
                                ])
                        buf += '\n'
                        # 材料物性の書き出し
                        buf += '\n'.join([
                                '*Material, name=Material-1',
                                '*Elastic',
                                ' 1.6e+06, 0.4999',
                                '*Density',
                                ' 0.91e-09'
                                ])
                        buf += '\n'
                        # 境界条件の書き出し
                        buf += '\n'.join([
                                '*Boundary',
                                'NALL, 3, 3',
                                'NALL, 4, 4',
                                'NALL, 5, 5',
                                '*Boundary',
                                '1, 1, 6',
                                ])
                        f.write(buf+'\n')

                    # 2ステップ以降の場合はリスタート計算にする
                    elif resflg == True:
                        buf = '*RESTART, READ'
                        f.write(buf+'\n')

                    # 計算ステップの設定の書き出し
                    print('times='+str(times))
                    stime = str((times-oldtimes)/100.0)+', '+ \
                            str(times-oldtimes)+', '+ \
                            str((times-oldtimes)*1e-10)+', '+ \
                            str((times-oldtimes)/100.0)
                    buf = '\n'.join([
                            '*Step',
                            '*Dynamic',
                            stime,
                            '*Cload, OP=NEW'
                            ])
                    f.write(buf+'\n')

                    # 荷重の書き出し
                    for c, i in enumerate(forces):
                        for cc, j in enumerate(i):
                            if round(j,3) == 0.0:
                                continue
                            elif c+1 ==1:
                                continue
                            f.write(
                                '{0}, {1}, {2}\n'.format(c+1, cc+1, j)
                                )

                    # モーメントの書き出し
                    for c, i in enumerate(moments):
                        for cc, j in enumerate(i):
                            if round(j,10) == 0.0:
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

                    # 結果出力要求について書き出し
                    f.write('*NODE FILE,OUTPUT=2D\nU\n*EL PRINT,ELSET=Eall,FREQUENCY=100\nS\n*RESTART,WRITE,FREQUENCY=1\n*END STEP')

                # Culculixの実行
                cmd = ','.join(['ccx', ccx_inp[:ccx_inp.find('.inp')], '>', '/dev/null', '2>&1'])
                print(cmd)
                sp.check_call(cmd.split(','))

                # 確認用に計算時間を表示
                print('times'+str(times)+'\n')
                print('oldtimes'+str(oldtimes)+'\n')

                #　リスタート計算用のインプットファイルを作成(rinファイル)
                if os.path.exists('./../fem/b31.rout'):
                    os.rename('./../fem/b31.rout','./../fem/b31.rin')
                    os.rename('./../fem/b31.sta','./../fem/b31_old.sta')

                # FEM結果の読み込み
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
                    temp = temp[0:num_node]

                # 座標値の更新
                for i in range(len(points)):
                    for j in range(3):
                        points[i][j] = points[i][j] + temp[i][j]

                # 角度データは0埋め
                angles = []
                for i in points:
                    angles.append([0.0,0.0,0.0])

                # LumpedPoint用のインプットファイルの出力
                with open(out_path, 'w') as o:
                    # 座標データの出力
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

                    # 角度データの書き出し
                    o.write('angles\n')
                    o.write(str(len(points))+'\n')
                    o.write('(\n')
                    for i in angles:
                        o.write(
                                '({0:6e} {1:6e} {2:6e})\n'.format(round(i[0],6),round(i[1],6),round(i[2],6))
                                )
                    o.write(');\n')

                    # 時間情報の更新
                    oldtimes = times

                    # 2回目の処理からリスタート用インプットを書き出す
                    resflg = True

                    # AMPLITUDEの名前につける番号の更新
                    ampnum += 1

        # ロックファイルを出力
        with open(lock_path, 'w') as lp:
            pass

        # ラグを持たせて処理を調整
        time.sleep(2)
