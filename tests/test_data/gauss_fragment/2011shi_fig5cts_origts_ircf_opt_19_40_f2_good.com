# b3lyp//GEN pseudo=read nosymm scf=(xqc,maxconventionalcycles=400) opt freq=NoRaman CPHF=Grid=Fine

optimization of fragment 2 from fragment pair [19, 40] and tests/test_data/gauss_fragment/2011shi_fig5cts_origts_ircf_opt.log

0 1
O          1.512227   -0.569349    1.514929
C          1.219359   -1.449025    2.569606
C          1.496837   -2.893940    2.185877
H          1.809749   -1.170541    3.450930
H          0.162532   -1.326863    2.832011
H          0.905498   -3.178537    1.314500
H          2.552170   -3.036297    1.946852
H          1.237113   -3.560148    3.012218
Ti         2.539282    0.611629    0.632799
O          1.470190    1.609611   -0.422575
C          1.350845    2.277279   -1.656811
C          1.280398    3.783763   -1.463526
H          2.194751    4.158836   -1.000008
H          0.436522    4.048514   -0.824703
H          1.153557    4.282738   -2.427374
H          0.441608    1.919145   -2.151740
H          2.199293    2.016296   -2.300627
O          3.398219    1.659307    1.801506
C          3.590462    2.809567    2.586139
C          5.054415    3.218249    2.608430
H          5.405888    3.451294    1.601911
H          5.671841    2.414207    3.012057
H          5.188575    4.103777    3.234086
H          3.242392    2.599299    3.603564
H          2.973789    3.623857    2.189057
O          3.794492   -0.210380   -0.367556
C          5.167605   -0.431360   -0.581976
C          5.584700   -1.824422   -0.138089
H          5.015156   -2.586944   -0.671783
H          5.415787   -1.955629    0.932125
H          6.646802   -1.982996   -0.340302
H          5.747677    0.326237   -0.041659
H          5.372290   -0.301198   -1.650774

C O H 0
Def2TZVP
****
Ti 0
lanl2dz
****

Ti 0
lanl2dz

