* CMU shared simulation parameters
* Copyright (C) 2021-2026 Gerhard Malberg
* SPDX-License-Identifier: CERN-OHL-P-2.0
*
* Values trace to ../../docs/. Change them here, not in individual netlists.

.param vcell_max   = 4.2      $ fully charged cell, V
.param vcell_nom   = 3.7
.param vcell_min   = 2.5
.param ncells_max  = 16       $ CMU-008 section 3
.param ncells_min  = 6

.param vrail       = 8.8      $ CMU-002 section 2
.param vrail_otp   = 11.1     $ R604 fitted, CMU-004 section 3.3
.param vcoll_min   = 8.0      $ TI floor, CMU-002 section 6

.param r_bal       = 20       $ two per channel, CMU-002 section 7
.param r_filt      = 100      $ cell filter, 0.1%
.param c_filt      = 470e-9
.param i_bal       = 0.105    $ 4.2 / (20 + 20)

.param l_buck      = 220e-6   $ L601
.param dcr_buck    = 1.65     $ L601 DCR
.param r_inrush    = 4.7      $ R601
.param r_pass      = 4.7      $ R201
.param ipeak       = 0.230    $ LTC3639 ISET open, CMU-004 section 3.2
.param c_out       = 9.4e-6   $ C601 || C602 nominal

.param r_fuse      = 0.5455   $ Littelfuse 470 cold resistance
.param i2t_fuse    = 0.0287   $ nominal melting I2t, A^2 s
