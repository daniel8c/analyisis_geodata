# 1-*- coding: utf-8 -*-

'''Script that automates the process of geoid model interpolation in various ways along
with the accuracy assessment using the arcmap software and the arcpy library'''


import arcpy, os
import re
import numpy as np


arcpy.env.overwriteOutput = True
arcpy.workspace = r'C:\a_sem_ii\GEOS_II\temat_geoida_nowy\narzedzia'
os.chdir(r'C:\a_sem_ii\GEOS_II\temat_geoida_nowy\narzedzia')


def geoida():
    try:
        arcpy.AddMessage('poczatek pracy narzedzie')

        KrigingMethodType = ['Simple', 'Ordinary', 'Universal']
        TrendType = ['First', 'Second']

        stable = r'Kriging.xml'
        gaussian = r'Kriging_gaussian.xml'

        i = 0
        with open(stable, 'r') as fs, open(gaussian, 'r') as fg:
            stab = fs.read()
            gaus = fg.read()
            ModelType = [stab, gaus]
            to_name = ['stab', 'gaus']
            for k in KrigingMethodType:
                for m, name in zip(ModelType, to_name):
                    method = re.compile(r'<enum name="KrigingMethodType">.{2,15}</enum>')
                    trend = re.compile(r'<enum name="TrendType">.{2,15}</enum>')
                    for t in TrendType:
                        with open(r'{}_{}_{}.xml'.format(k, t, name), 'w') as fw:
                            m = re.sub(method, '<enum name="KrigingMethodType">{}</enum>'.format(k), m)
                            m = re.sub(trend, '<enum name="TrendType">{}</enum>'.format(t), m)
                            fw.writelines(m)

                        model = r'{}_{}_{}.xml'.format(k, t, name)

                        geo_datasets = arcpy.GeostatisticalDatasets(model)

                        geo_datasets.dataset1 = r'pkt_wsz_test.shp'

                        for N in ['N_M', 'N_RES_M']:
                            geo_datasets.dataset1Field = N

                            arcpy.GACreateGeostatisticalLayer_ga(model, geo_datasets,
                                                                 '{}_{}_{}_{}'.format(N[:-2], k, t, name))

                            arcpy.SaveToLayerFile_management('{}_{}_{}_{}'.format(N[:-2], k, t, name),
                                                             r'lyr\{}_{}_{}_{}.lyr'.format(N[:-2], k, t, name),
                                                             'ABSOLUTE')

                            # Walidacja
                            inLayer = r'lyr\{}_{}_{}_{}.lyr'.format(N[:-2], k, t, name)
                            out = r'walidacja.gdb\{}_{}_{}_{}'.format(N[:-2], k, t, name)

                            res = arcpy.CrossValidation_ga(inLayer, out)
                            ME = round(float((res.meanError).replace(',', '.')), 4)
                            RMSE = round(float((res.rootMeanSquare).replace(',', '.')), 4)
                            ASE = round(float((res.averageStandard).replace(',', '.')), 4)
                            MSE = round(float((res.meanStandardized).replace(',', '.')), 4)
                            RMMSE = round(float((res.rootMeanSquareStandardized).replace(',', '.')), 4)

                            if N == 'N_M':
                                with open('validation_N.txt', 'a') as fa:
                                    fa.writelines(' '.join([str(x) for x in
                                                            ['{}_{}_{}_{}'.format(N[:-2], k, t, name), ME, RMSE, ASE,
                                                             MSE, RMMSE]]))
                                    fa.writelines('\n')
                            else:
                                with open('validation_N_RES.txt', 'a') as fa:
                                    fa.writelines(' '.join([str(x) for x in
                                                            ['{}_{}_{}_{}'.format(N[:-2], k, t, name), ME, RMSE, ASE,
                                                             MSE, RMMSE]]))
                                    fa.writelines('\n')

                            # UNDULACJA DLA WALIDACJI
                            arr = arcpy.da.TableToNumPyArray(out, ('Measured', 'Predicted'))

                            min = round(arr['Predicted'].min(), 4)
                            max = round(arr['Predicted'].max(), 4)
                            mean = round(arr['Predicted'].mean(), 4)
                            median = round(np.percentile(arr['Predicted'], 50), 4)
                            first = round(np.percentile(arr['Predicted'], 25), 4)
                            three = round(np.percentile(arr['Predicted'], 75), 4)
                            var = round(np.var(arr['Predicted']), 4)
                            std = round(np.std(arr['Predicted']), 4)

                            if N == 'N_M':
                                with open('und_validation_N.txt', 'a') as fa:
                                    fa.writelines(' '.join([str(x) for x in
                                                            ['{}_{}_{}_{}'.format(N[:-2], k, t, name), min, max, mean,
                                                             median, first, three, var, std]]))
                                    fa.writelines('\n')
                            else:
                                with open('und_validation_N_RES.txt', 'a') as fa:
                                    fa.writelines(' '.join([str(x) for x in
                                                            ['{}_{}_{}_{}'.format(N[:-2], k, t, name), min, max, mean,
                                                             median, first, three, var, std]]))
                                    fa.writelines('\n')

                            # '------------------------------------------------------------------------'
                            # CrossWalidacja
                            test = r'pkt_sc_training.shp'
                            out = r'cross_walidacja.gdb\{}_{}_{}_{}'.format(N[:-2], k, t, name)
                            zField = N

                            arcpy.GALayerToPoints_ga(inLayer, test, zField, out, 'FID_ONLY')

                            # obliczenia
                            arr = arcpy.da.TableToNumPyArray(out, (
                            'Predicted', 'Error', 'StdError', 'Stdd_Error', 'NormValue', N))

                            min = round(np.nanmin(arr['Predicted']), 4)
                            max = round(np.nanmax(arr['Predicted']), 4)
                            mean = round(np.nanmean(arr['Predicted']), 4)
                            median = round(np.percentile(arr['Predicted'], 50), 4)
                            first = round(np.percentile(arr['Predicted'], 25), 4)
                            three = round(np.percentile(arr['Predicted'], 75), 4)
                            var = round(np.nanvar(arr['Predicted']), 4)
                            std = round(np.nanstd(arr['Predicted']), 4)

                            if N == 'N_M':
                                with open('und_cross_validation_N.txt', 'a') as fa:
                                    fa.writelines(' '.join([str(x) for x in
                                                            ['{}_{}_{}_{}'.format(N[:-2], k, t, name), min, max, mean,
                                                             median, first, three, var, std]]))
                                    fa.writelines('\n')
                            else:
                                with open('und_cross_validation_N_RES.txt', 'a') as fa:
                                    fa.writelines(' '.join([str(x) for x in
                                                            ['{}_{}_{}_{}'.format(N[:-2], k, t, name), min, max, mean,
                                                             median, first, three, var, std]]))
                                    fa.writelines('\n')

                            ME = round(np.nanmean(arr['Error']), 4)
                            roznica_kw = np.nansum((arr['Predicted'] - arr[N]) ** 2)
                            RMSE = round(math.sqrt(roznica_kw / len(arr[N])), 4)
                            ASE = round(np.nanmean(arr['StdError']), 4)
                            MSE = round(np.nanmean(arr['Stdd_Error']), 4)

                            if N == 'N_M':
                                with open('cross_validation_N.txt', 'a') as fa:
                                    fa.writelines(' '.join([str(x) for x in
                                                            ['{}_{}_{}_{}'.format(N[:-2], k, t, name), ME, RMSE, ASE,
                                                             MSE]]))
                                    fa.writelines('\n')
                            else:
                                with open('cross_validation_N_RES.txt', 'a') as fa:
                                    fa.writelines(' '.join([str(x) for x in
                                                            ['{}_{}_{}_{}'.format(N[:-2], k, t, name), ME, RMSE, ASE,
                                                             MSE]]))
                                    fa.writelines('\n')

                            # Przynależności odchyleń
                            cm05, cm10, cm15, cm20, cm25, w = 0, 0, 0, 0, 0, 0
                            cm_res02, cm_res04, cm_res06, cm_res08, cm_res10, w_res = 0, 0, 0, 0, 0, 0
                            if N == 'N_M':
                                for i in abs(arr['Predicted'] - arr[N]) * 100:
                                    if i < 5:
                                        cm05 += 1
                                    elif 5 <= i < 10:
                                        cm10 += 1
                                    elif 10 <= i < 15:
                                        cm15 += 1
                                    elif 15 <= i < 20:
                                        cm20 += 1
                                    elif 20 <= i < 25:
                                        cm25 += 1
                                    else:
                                        w += 1
                                with open('odchylki_N.txt', 'a') as fa:
                                    fa.writelines(' '.join([str(x) for x in
                                                            ['{}_{}_{}_{}'.format(N[:-2], k, t, name), cm05, cm10, cm15,
                                                             cm20, cm25, w]]))
                                    fa.writelines('\n')
                            else:
                                for i in abs(arr['Predicted'] - arr[N]) * 100:
                                    if i < 2:
                                        cm_res02 += 1
                                    elif 2 <= i < 4:
                                        cm_res04 += 1
                                    elif 4 <= i < 6:
                                        cm_res06 += 1
                                    elif 6 <= i < 8:
                                        cm_res08 += 1
                                    elif 8 <= i < 10:
                                        cm_res10 += 1
                                    else:
                                        w_res += 1
                                with open('odchylki_N_res.txt', 'a') as fa:
                                    fa.writelines(' '.join([str(x) for x in
                                                            ['{}_{}_{}_{}'.format(N[:-2], k, t, name), cm_res02,
                                                             cm_res04, cm_res06, cm_res08, cm_res10, w_res]]))
                                    fa.writelines('\n')
                                arcpy.AddMessage(sum([cm_res02, cm_res04, cm_res06, cm_res08, cm_res10]))


    finally:
        arcpy.AddMessage('End of the process')
        pass


# uruchamianie narzędzia
if __name__ == '__main__':
    geoida()
