#!/usr/bin/env python3
"""
Sum up 24 November's world news in one image.

Deterministic, offline generator: draws a one-page newspaper front page
summarising the world news of Tuesday, 24 November 2026 and writes it to
/output/entry.png (override with the ENTRY_OUT environment variable, or
MAKEFUN_OUTPUT_DIR/entry.png when that is set).

Pure standard library: the grading sandbox has no Pillow, so the
letterforms for the frozen texts below are embedded as pre-rendered glyph
bitmaps (4-bit coverage, zlib-packed) and blitted by hand onto an RGB
canvas that is encoded as a PNG with zlib. Same frozen data + same code
-> byte-identical PNG on every run. News facts were compiled on
2026-11-24 from that day's and the previous day's reports (Reuters,
Associated Press, Al Jazeera, The Guardian, ESA) and are frozen into
this file.
"""

import base64
import binascii
import json
import os
import struct
import zlib

# ---------------------------------------------------------------------------
# Canvas / palette
# ---------------------------------------------------------------------------
W = H = 1024
MARGIN = 46
CONTENT_W = W - 2 * MARGIN

PAPER = (248, 245, 238)
INK = (18, 18, 18)
MUTED = (92, 88, 80)
ACCENT = (168, 32, 24)        # newspaper red
RULE = (30, 30, 30)
LIGHT_RULE = (196, 189, 172)
CHIP_BG = (238, 232, 219)
BODY_INK = (40, 40, 40)
CHIP_INK = (60, 50, 30)

# ---------------------------------------------------------------------------
# Embedded glyph data: one packed payload per style. Each payload decodes
# to {"space_adv": int, "ag_h": int, "glyphs": {char: [advance_tenths,
# width, height, dx, dy, hex bitmap]}}; bitmaps are 4-bit coverage rows.
# The payload lines between the markers are produced by a build-time tool
# and spliced in; they are data, not code.
# ---------------------------------------------------------------------------
GLYPH_BLOBS = {
    'masthead': 'c-rk;OY0*y68|nf`_O8==eDp5IRpYB5W*6IT9T8)9s&b_5c1vAZMWTeRF$f;GYJHXxs3n6ZcFuk$-iAb{v2ZdA*5d}AB54@OZf4JpDrJ?yIy|$->*Oa^zriHx68jSAO5SXy()KA>N;J;ikteCZu?p$&eFHnnmPDz;4K3#@_|nbytx%ijq$O>`ypIz+j!yg5bsu$K8~PA_`IFc-?%K;i0>xFW<hvB5|afR@#B694h!u5M#*HsO8hKpF8BfQm)94KS>Rt3pKlx%<l}V<g9W<Su3@lXDacWXwIzt30JTX3@g1a=3YYx3Iy}jOjrg%4F2#cF@22>FA*2Q)z5wkI$b#*Bp;I-S1<Q?CmNYy4N+9uxr642gU9)gQB*8C@C<{DzD2uWngG4Kcuyn+a6G`N`{oK;N!xbNI+FHv(FQlnC*MbUR&w_->U@4@&`VihuDWtjj(m?owh6Qsbj6kuWxNTu}JJWLvu8}I^mr82$Vudb0Xjlfw>3kM{`TlzO_cN|g+dpv?=6Z>c7UY~_@J3QDxO-+XCF!+W;~Wa^XH3M>s$o7<B+3pU_VeV@rh*(ZiQNRTkk5I5o#x}!Ner+hco|_Qm3uwMu%#UrBkbIJEfiZAgEYhz?o*DiqO;pLws#@~Hnh4-U<*AKBW!m#0^7N50;}4fhKDtu39COP_6!}m41~bi6MXBUUY6{P<t(0%-^|wwc|zap2|Z4H`=I)W3dP3$a}4`3QCW_#2UHF0uZ|G3P}c07wZ>RixQv$zSp86<Lqx;#Z>xjT9ACKldrPOY;<=zdZhrbdo1a$Gb^9lGKb>yll`A_+<3|3uij+*{oA>4Y>ZI@Q$U_;bb2btenYh5jStd?1agvD>YY@f3O`}-l)8oRjaB!Rd=HN6F=a{&Kz_shI!exJ~%sfY6;w%%Vm^d!qCS&d2B7bLb=9%OTaQ>N{4shw|_Gp~o#8tceb8wCmPwlQnF>v`6Y=HLpZlc5T@P2aW2lu#)<3F~TjETGZvoBVEriHxfkw4RD{<@yv{1e@obM$r(42)Y+<KF$Az#1ss>yofV@Z|T1;KKBN;{C)w=?QB6eNUveT<exM2j5S;pE&sh;Ri+M2en&pU+a5cYsFs?0c_F7m(Ofk9MMN)c9$kLu*;`&3@-u@&F?5aNd)}{zJYJx8;AoVqv-z3dIbk)IPI6c4w6{F{Q8^*DpvJ=&$vAYn2yFa37m^oUEv;0vFw_5@2*f!%&c2Z%yfF@0>z_}{MDX$D|1!)DuGEdp{!qG%Iiu?u$pj3!YticqJv%B?2%&!2@J%%u*n-Gl`aDIcECa$?FdzT+v^1qZpM1J?^<>gj)26q@|OFy#=?lEUSX4In?qpRCbYvG3mG}cruPL6O0@4vO;Zi+1k0*j2U`?dG06|cl2q08O7x6T**liye~`{f*+*A5irO_5eBWmzh_aO3WJF2I@vkr(ek*6Q&Y*9_uJU+-MJ&UiG#Jg;i8!}!e~KpO=xt8%Ql5|#SIVFs$)E;W$B-j=wZh#g-H`)kx_VYC(gTl2cXh6N^oCT+fHsE#1CjS{mYLAw-uycJ<<Or3M#Pu>E@yo(xCX(6Sb}~hwzO60C`V}}rM55UnH@wc*s<q;q>wuFzSvT^q+GM`n4f-L383%%buo8N*6G)GtS@nTrgR3L`ck93x$Dns$_eJZ&rwDui{Qk@(&Oa~r2m#Nc|>AHix~kd#>|LfWB7phMGTK^2*Vr1E@5~L){#CP{_K9vp7$(06XMGdyvEEt(#K7${Uq@ckEuGmkY<5LddJoGY^D=<(1781Cuslo(D%spmyh$#gNq#<eQZB#Nz*@)Gw{H?DtWB{;P2tovt;G|iHH(Fdq~`_0p-o(5fLoU#R&GyvbQ&ksH2%OroI;?=$fcwdsPz^tr-NEsAy%qyv^`Xv)Oia<+7}-o5?d_h#GmbqkH5#!Z-IT?iKZKo)vX@#0iWl$1{-se9*1texC(2rpW8;w(i3a4@wqwrZyIDbA=5W#!$aQ-5Bb2s2xMi4%K6*-l1{~l{<7EL&XlA#?U*g8EM3zz~tjR%=6yRH}nmCL;nnvb?w%;u1lR3Z=rY*%T)gybn~d+t{&Bx>1y<T<9qd}(6fVk(#`bt|NR0RQX6{E?do!@E(O!Xm7HtjFV}m-h-7T-v0?K9Oh)q=Dgdf_yEAbH1LUuJxIROLN92}CyR+0l@q5b>+}YeFc10lP;DT%Fb7u(`PZJWfsurHG@L9oWeQ00nuo|leYnWALp#g!1i`8X5>S}OXrPjl!I@R0tc%3*PQMRu3rHKN$=taEJ69?AWp&Q<tyyafT(ha;Kn>ulRXiUeS8Ogc(JKzi41hGgCE?bVx4{_<vwjeoqmmoh?wmI9KHHPkgJ@h2)-_%?q)TrN?>+DcJX(ehh2E6%SUo1Z~t`-sE-m)#FuCN)E)mDV(6y-FgD>N_`<aI>jsqAFk4<34prxH}90!(A9R6f_AOSG|_5$EiN{vFJ!LC0|;e=?)G&Rxp;!u8%6nTyrXg|5*V6jIU;%rGnBLN>9^U=Rike#pgRjy_Q3Ip_=?`-2(8E(z-?Mxvkyn8t|7`S90%B(~9=jN>pYVx;ziAiCnX!}b=(5#UVrE4w#uG4yxO?v)wMd1|-}ZO)-}dxPY*<qOX}3w!jWQh0n^G}a*+s7AvisrjL;qk7`yvg1czX>7u8fvIpJL*>q7*p7RNFn-n7YS>~#xN{L<suol%$Yn5d8X#krFtsbGDAB+fqT)h@h&>h65e&^^7ZS1f8K$CnMv7u&Q+EE7zl73I(cT4<{5h(kJ(KTER?RVxw>@HwOoPlyfa{+nTX>d|o+5!gWMHJhk?A(y=r@{;E}C9sF=v|#ZDv=upE5Fn5de>Lf`Pt#|NHNM07)wZe*',
    'top_kicker': 'c-oa!O>5jR5dAMcyC7MzZ0)U~9~4Skdg-B*AWNF$&_f_lC?Ws7^JXOPCfPJZEbC``H1j<3W^^~)-lSYFQ~5I-{4x&d>hgLx*f0)PzyID`-wubn;mvUPIWOZpy3vf*j)NznDt|`S@M|32vXPzKXea#4=*I!C7NX6xm8n*%&{0Vg6t5I#%8CnlQ)vS9@SbP^juefVsQ_2f<?y6tUX@l@CcF)7WGl_UeD$Go+$e(PMW<<nDQISRt9A2WSi~Ri&v0sNVfqR=LWiy}_pCH(=-Uc#vt?$kK_(pbr!;q4{$lk|^P(Aicb-};+pNherAju{+fw<9o8y&eYS7Xijw3Hm;Upy5wrUjy<nTcVM3%sy_8!zMQ!@{<hUH}&mhZtj#m7ijHhsrtUfR(-$30pCoe!X6{1~6G+4`2WdpQSmt=)L}ukm951|Pw|ad3C4cApAYOJyBJRI2{Kv8?pM0*PxwtZ9~7^zLB6L(`@=h};zLoSNB|nfb)ev{@`}*mY#r6BKX^T7@d;)Vxkg`4dy-4tFOxTVMQP<L5Kkenq-o37Rr?v4Fvsvz;NyB4Pz=Mg?-qcbFtk0$G`%Lm49qc_^$MI;vBH-0874I92KpUDhFw7P6rB^;sck_vo$@A)s2^y74H4$X&P#0l@7-V8NW;gx$;mbRk5{xOsQIo&-&%3!$Xm%-^1A=33Z6p8=%}246)7IziK8<Yl($jyBI~S?!B$-4W<~e`X@{U<_RllD^}tbH`EUAB?hQyX?c+wP@U1z6ahQ0EJxLrTdNhFhq6bu=oLLfzuTB;$~D%8d`#uC^d*$-VG-i&Ks_Nm7zOZl+RM$_%fkKGe`6kR~DowF>;OgX6DO&%57-*!ltu!Ih+-~$ic`CP}W4No`;bN#tI*NLJdN|x3WUoDcFu_C>9yNzyAm1fG)!',
    'date_line': 'c-qBQ%dXru4E+~xy75A9%l9L?>Mkt;J*cEWnqD+bfFQ`f_mGsv(<HZPgBJA+JjY{6JR%P%e%RhTmPXG@f44nEzi;Km^OxI$J@)OztM`vD-)s*bw(quwXFlzI54+jpzL{|v%BJIcY(MSWj`x_$@9l2WzWI^yH96UCd4RzHYtnAbZv9-txU*AB#u(fC5l@UanH-)^+<OHuejJwn$3+DXf_n8MDQee$*SKpg*7HDxtlB6t+D^Mn%sokrM>^_9I!EIrgxClsiRn0^(d!sqfulM>?^Zydsvyy+uhOJzJWXI4CAqvA^E#PWSj6ldG1=*Gb7me3dMXR{GfkMgozPP>6ZT>z%y5cAem!Ac9ENd$uRKyPi~BM>A=6A>@}EhKdbUEb#LRy25}nkX+SQ%6wH{(yi3%1St*3Yp97y8v2#58y0$WJXDAWImbx<k8M$;`*Kdlh^o{9Nmw~mQfCYDCO(NAN_MQ{<BD0XU2ag=x|Rt-#Sc~cYPH{P&m;&#Q3&bTmqao(`$bm4$FGUXqbGO|Z0i!ZNu4Cf(|V>H%^c+kQP>-s-1Q!aNZHK3e1{JzZefwEeJgtA$gUFo*WId~UG?L>oN898`Y0H*<kS(f1eol-a&1Zj;Ewb({ded;7}?w0FM0Ig-_FM%yYmBZRHB!|Zt>{NuB9p}<py}<32l%R;g*lS4CP3=w>WKR7qFSuximA;q~zJ?NHd@xF*hFBX=6X^oMv{s$qRKe*U&9@mdde>?ptHjhQuYB;zVFac~cNA~2a~!+8LU*vrt0XKI=M0q1XSYOI+$d5ff}d}VSu+BX-BU-<BsqCy92nxA7oT`XOrvPD6eiy&d}R-o?)UY#cYQFkR_3l-ynM_RJDz6B5k)$NB5MW6Y8?zOzg1KxG~fYhj;spR2~4VTz(NQAQ^1^l2B+Y5ccWA(W!=Z;AD-~)(+P#1{_uofc-Jw@c*KSSQyTIFf%B;8$&_CC7|p2CjrYWxBR&Cf+UgE9W+N+eIg0<aC#LxN3e3fDI=%k~PXF~wY2uOTa>C6tX;+%WS-v33sZf-S3*D0FoHGs_9$F`*f8dqdOq0hyYY>)ezlzo&=j2s~zNu*8Oj`?nUER#-H*iXRPj}vTjo9@iV`P@X?c{#Ved^8&qQQK2Mh&NW*YYu50}o0le>j`9eaf8PGl_j0RP`M6N7Y_I8zEoZluSqM2`9G9{amk6%>Ayds+_V0KQK2nB4^MTgy93_4CO>Sn5XVe!hNC-v6ZyVefya<Yu6g(zX4?ES0vJhmzsz`dM#$NguheY-AQvEu#o=jP&pk%a?&ZEv^u}QueDJ|PZ)G?CLMulJz_sso3=XKLmMcz{Qj~WKCv94cISL#i2=u!#a{<omRx9(1=y!o%Sg7|R|nhkY;b9{oNlaM(cc>HqT?;fk^U9AK;4A;<6EqMs9O2sxJlXSFm=o^A3y#9+O<4d',
    'kicker': 'c-pmA*{U2j5dD{a?guR`sdeA75kgk75S+vqt@cA63?_kK{O>tcC27WY##{nU-{Eqmrz9Pnsyfo!?ak{{+KW{G-X0FOZ|UWWSKEUIdim!+uV1~{9^P)BY!AO{?RRbHqjtM*3Qz9+Q1a;3dK}pI*xJCkA9(~Jgnk+!N$K83h*PR?kZzry$RRc3;h@|-MOFkM#1K9a<a^;64g_t__wCb3Q!!JbS!udfg2v#IQf@s1VL|13H-gMUCnl^yA<q#NP<{oCbD+@kdY5Kgv$9%Emg#(USG7<Y_%QF%d#$Y(O)EDD02-%Kt@F<oQMSu&WtUyu!`Cr$tSO#I@|*=)E0wTTk+q<0ZmbE@{QSOZt(=A=uNlKI5${*0-i8`TL>L;xrAFxG21Qb6jPP@os;_4z(V`JLUl1J?ZjwkjVLJ4jBZ*QK_mDhxjWAD+khr|YcBb<s(J}5(5=p?Cj?n}pEG15osC<np5swpen?y%Td5N(JQhAI$l_=*aiA3?B_iHWAqHu7c+E<{7?zLB%xhFp~@avg<eLa*)h*(IvDm5fQEwx0jAR7#Q9$g3p`)F?fbea<wNf$H4E*#B}SGaWJF|$F{LDaqhwRrCF5wYvEeLNu9w=?+%5%`w0v3BHsmf|6O){zp<lkJRa<*KiQ6D6~>OxU9kbWe<J%h;)BtaC#jXu+YoR+M1V;WGo1l6K;=S2giLN@t<@-Mt2`Vv=Z4E<{GH>4B1zYamKZ3(_ZE3W8N@LFBUo;bjy=ML7@&F;D;^I^Tb|V@|CuR@CgYD2Pzita?<1TOE^oTpa_Kxx&d@#i+W*9;0Kll;v2fa;PKQJBRK4@ByD`#c@3p_!oLkN+g1yAW+i_jdzKU4OCE_cGg=y)RT@g5z+baULVS7Vg?`5Y}%Nv{k-%`yu1x7wk#WrbG5`xJDYDYj1oJ#e(sq!P1JsxO6jYFl9s$l(mSWZ>12~qsRqjC+#M3sf)!}k>%};gi}Y=VnJhIs98(>Ilg34l*$c$wSUNx1dWqW4ViA%<W>%(q$Cxv|psB-qzWYBRV)M&;ITWFWUr@t+G?+Q}<4WWyPezH!Lf=LQ1Z`QzDj6bbzY;YEUVc%N846#p9R5eHlg4dzb~36$nHUF8plg!Gm5VN3h_Z4Wi!hKfu5t-MrP1f$I-^S-3=bh;7-h8pzWX#yGyvEh#XztMgI33h0!OKGO^UND5|;!Q0&VNrZE1Qbql4rqECk6#-!*Mhj~7MsgZ+hBckxn<y2<e-x3utIAyND7rZm^h0t||@^IFZ#R!Q>?UA0=4Hs&4|>_r&l?evl`f9r)GXnuW^{qYwj51{1iPJeno_suyY7Xc+9Mrn(XGvdr8&fvbyY5Z}@W4Gt;-u(+aSwYM',
    'lead_head': 'c-rk+Nv|X|68<lBu0wja`#5vp2#2|i5b~BVq7f}MLK-3d`=s{>+gT6LAfcx7@boIecG?l~#pe9w@$rN8@f#a{e!L?@JRkPkZ@zoH<Hz&y?fd_J`0nH5-7gRFc=vD0jwjL2>o0o}@_Zci(eXURF&+`l6H=%<Pe>tY0;H4)fWpr+I)x}sl7rxN(o&x(e?EmUUUgvvqn9q?i66tynezDh`C!#%C`mR$s?9KIoDVSuZxyX?!1EpJ#HfW(#X2IdL`U+be4&y;l-1PA3c3*6@?~hq#MlmL%KYm;=1n){GXFr&7zv(Y(+<%{5sci-_FxnhWwIxo)+8Dfm|2L?2?B`rl3k%&ir&NOHU-|NEL67Jz26Nzr)3L~9}Li|m<5AUVV!ugc}+&4SX|Y|MYIPt0hNp|)&o~VOG3^EmYhp_4#8ua3*`k=D4Pu|2B&#hC|Tn_E^B0m%I=Fik8F($uaJz=nJ#YX!nr=tE~oSAdQ2TW6d(%0LOU3mz}#x1{pZB3_=|gP{dw-W{3W;k3@_iS_uQh#NVi=6LK;-X$yUWI=AePqFI;aWow->H%6Q~NmOZoTP2`r_AY7cy!fo>Kdu}r)y5&}{dh#vzfC2D#&VBvf*Lx1o*U#Jvw&EU1TS!WAJvt2A*dwJWfo(t(hVuuWF+CJ|yNuj_Cgd{uq&fGXDEBxBSGJ)2g0A8OI>b3nh3e-?Jy&#E3aM-u(&N=UhV^k*d8{lK(7sjXk${oV)xx?A)pXRvqj48ml1^B27iQ*ZM_aVu$NE&ye3A`Mp8MB<z~^^7b8ccCwva8)EjIq!=9w3JQ7_KGU!46`W>kyzLc6}qHsg(C*`)0|)yu)nun9ivHmQ_`O<3kt-PF%Em}9#c*><*Fb-_^9sH2zEx&h582#Jmrt0imr`Xb>=T;O6Gd|mO>xIRfNpp||GnT7d^j1XxiOaiM&1V^R$1pPdIgE?Zx0Jj5PlCnnjqE_3~$lq^_P(xrWI6Q<`(1Gs2_$DIXgyoyqd=pH+ZNMw2-mHLQvRXmQJg~(ew#Ot5dSrwNvID%n6*U~NRTdnuRX0j<^aj#63-T*;@c^=pnDQv%X0uoGYZZohLmAi?QFG9ZUQcGou6(Em#{u4i`Y#*m=?3);^w&Ji$!hwy8Sx0AL5nM0uQAw>>0nV}>kb?V0(wmarCCb?wc2JNKsmb-Mh~N%&^$^>x75PGCRC3ilSEnq+9J>l<rYJ5Dt4^doxZ_o%MI@$aotucj_eIzy~TfP{X0+8_9t;MF`tjIH{{b^M7Q#F-3^It!l3#}W{w6ugu6{N2lmlYGId)l7X#ebXRm@L`!1Uc10prNBYar2A?`4~3|lf~p?CO9xc(}2T{L;pT<Y%X+%(N7_M*rgZHT5(P~f&;ETFN72&I5n(?D!ubxpQm!Q^UUDPYGFOM;*KSvwXC922XWoZPVDT6Vd0gP5guf`a00VPmOzqamBnn{+A31}ba9@`<vVQ=M}_0}VSkwK#-Prs8_@U!YUe5X8?HPkfW>jaI2_)~!`_J(tRD%v_Egksq!jf-dIFRhdg}xH56$al_?_8}7LDa*$HoaSth1=XsNye&+s-xkR3u>aBLMBLb(~r4!>eVPMm?I|Z7q6|N|E<gArTeO0z8)Ad#?U3HvcUQ{O;VGg<5*pdnlT|$i5$yBPrUWsn|5PyKm+bIB*&jmIeS%_u?t`J7<GN>G+tb-~+A~vXMONI9WgGxb&Q)7f}D(xDkqu@!V!fN`HuP=m6NsQq=0-ro-IVLS1{7DSba%vpAkQ@75jHAgHHK@KEFP#V7L%8qB0c*!lJvTLN<GkBVX!gT~DG>@pQAl+4{Y<Q+D#P44Ef3ik4+q&0ZXfV99hYkg>^9gGo2#ta6QUf{{#PQAu9h5ZGS$+(!8zBG!K&Ul`p=~&LiLl-R7R4g$!en3w~8?LOe@6TjadM70;HE7YdtLY(Tn2`JPk2P<*M4D2g%&0@V{>O@&@`jlGO5jf{&0-D!N*rNO1Oq<g@Ad{7o1P3J5Ytz8;7rf5c14afgc-S25J@b|K^P+JS6depx+;k%K`IeK1n@SZ~geTh4KvLHz6;D#M+#kFdS008JIZ2&`7fX6nB5BC5B&zySji8(>J(o`tgVuu$J9%C2I!-BrpC4mE1iONZPJuQn>ow1EVh_sE+a*_$<J*$g@OYXABF|KtCy!5O_KAZ{kL{E*5q&7Mq+WS|*tQZG0DO8aU^lPRI7wO+FVbM#K>1t-!o1`mxZfSS<3@MplFXayy*nUmp^wsM}#)`%?IfFO=c7B+QZyheipyo3eah}%KO=Rtq%LBl`Eaf23971VCkFJCp9fVL-T#fuN?)Hx0NaeQcn)8(47c`N7sd(8u(M~;#go&^;T?^TZK*C&3QEZMzUV4~W76<EpPytNe|bo2cI*%2v&nXnk&6|E!5Zq4o6(LQzC=k`P-j+8Za%nvC^uo9N1*+^c3Dmm9c-bm1b`p_~sUOrYz8kM~OtW)aMF00=!oS+nvsP7)E)(+l+oy)0n)W+Zajidq7W%qcPKK$48{a}CdMDK~jL=VmAe;3`{tgmnOBX0IjXS(Wm-pNPIbT#4|X&Jhb(t?mfmd-A^Co!eYa{UV#a&yH@wznaFHF~$t=+Q+6tdiCA$<N1>iYfCX5_`04_|d!4^5!6Bvy$ieD<%sY)9(b>nm=9%Hp_M!y2E3|@L99z`a6jEUOsmxz|~OhG|&U3kJXd9`9u)$wc&5$bdyV}|F<fjj<(Z7;c0}?Bj<MIGOm3;NApQ_jwh5b8S<xfYHof}X<Qbc5lzlNB{>V0<t$UHTeM4HgFl1Kho4K1xz{jXnYFHl26~dy$G-9)LbPkW>!C}x?GyMte_6}sd)S%+gbVlt+!2DSO6gi4e|-Jxum1y!BupL',
    'lead_body': 'c-qZaORro<5&kc;VKbn9oPK!+QI-f6VHKjNpLRk57EVA>l>g3GRo#8g*w@B3A<EI{-s(Bs)nC1<=EvKsm$~*YbNkornTz*Ze*Wc)+cOR7`8PkjeDUh`?8n=0ZqGhH)ZN_OUElrv*6`F?YALrb?zcPM;-uxbbWn{>AKR2KsyaoRez!K6xk-<P54}=&rFFP#yg2TPE>KE^+Iu-bs61+nZ8)XeNLcIEwJJl?yD+@!jVNVD(xWhm|7K(+)u<Qpvf*+JHyB~&)WMr|qnC*<?hL{MPPU3=(F?F5z<L69UAX8xCe_<9IVZjDV0nH%%0^O6iqZKopF|MNQxHj|)#Fr!V5vdUFcmsXYRov2n)ylN5JFEyDP6l|!c3h&WH|*sMNcBhX4|LIaT(yz0|i|n+P9g#6(^vIfCQ8<QL0=Y!6`Vx)QE}m?lMN5Quvg6^J}Xv=P~k@?Ex7ey(l#Rxm-*)=}0OIV)pcePI&|Qg~07lOd65pZ>n`AIz8r1ZiM-rA8ATeN5<J4V#~k}JM`)fW+D5$vQsJ@_=E>sgg_1%5v2G;i&`N5o**8A@6@S+S8uzLl!&ao&^^WNRKRNOGNDopIw*ZE9I42Ssm<Eg2G(E{;~!$2`EVrlD%P(ET8^*@2%@ybnqu)duZ0tqVNXkOmifaH&1~%-d`oZnAchT>q|yQKm;sOPHm&;Dw1#abZ3`@ROuW_78O95xhVyJ1e$!@@3tcaJl3<9r!7vlscAifNzBAJ@D`(h5{*{l(VbnwtWXV0O0aKtCJGx%cl%Sq)+7g~?FRM26TUX^_XWTx<*Yv)8AY~0ZHO8b9C(PJK&5VrsS&oWCJ4m!omu2j0mYGg4)k4o{n`xl;T<k|(xv7ujwi(1L>!C@QKawy3mCRj*38zM3{gn`L8YOD%tb#g<Wtf>y_ee{h`>a%k-yXuO6-BIq;!1;UbICE35g4-6V1@`?OT5vZ%s7`gS1APN67k6Kxt2lvW-YZKlX&_Q3F_@t(B+UVyXDheJhB*ZNi&_IvKsX+MUg_}%qZ=_^C~1Cm+XUd__(ZR{-MqBk(E6!;*=R@WC#pe&#;*#NW4>GiUj@h+Y-m%;5>u2>g^|x=*b{Q$FgZR@}#vxLEN6y-AW?C=||uDP@3R>M(|CX(Zwk}UYyn)oLo_S@L2U&!+%u^66P-}3!bUMU20wYr52}>(Ln0HvMc4%BuQ>&zJdrR->SUB7u4F~r!aZ-1BQASbx#yQ1`T8928N1s@<AffwQy~v<TAAau2W)zL$&DK(THx6j)~Ud<`P4lOJ-pj2z_YOM_@0mg*ThpBSEVKO*w8=HZ+YrEgQZX{YFPOC!uDMV9r`B*QtFmf46bBU5TWC7|JQkkDEfd!?J$brNMIm;bt=;Ezx_BD9*iDB2k{AM>-wUUO9#gQj~$)j|DZIWPJGcvKPVaq^KNV0~4j5>9&J!qx?(Y`vv^g;AJSOq<psRY<a1_nOTpTws9Fs&Qds<m*==BTuEOC=7v@2eU>pL%;u8;4H=;PMVCjVKCVGEN(LLAbh5NE9!>Be-+bs_y6*XF#$)-(AlU>l$WmNpAM)c=aywO@pR`SS*gFlv91b#cYGM$K0!hcSYoU?HaXZg}#PKDAA$P%I83O;}(y7x>>L_O(Z+O{TD2IEI129gs2vby0T!FYWg}G^-_#Y_(`xOn>;chQbtuJQx<L~~kyk83ooKN@PYH<$M+vc;mee|D<$pAS+h2ETK`EQpb^Wj?N@v+Q6?^V77p_wv`RgT&*6HdfXEro>Yzof@`V)5fZ6wU=(g@Th90{hLIT0Y+Y!}5N+T0_rKK_P+3$yb^%5gG7R%83=3b@&!TK`2E|18y)BC{O&yNOHhLH!(`M=X0I^Piqq6@0Z{>#n?_C-|6)3XL9;~Je6K$+V(Q*XU`g3(+;KnnKG%8&-996Y~>V?XVT5ry_<ujES((Ec3iVPS84+E^0kx!KuL_tX3Z@C&ejSt*5v9&npy#XDdTI@xv$QY7)PmLYWdiAykF=L*na|SpjL1h5Ktq{@hFi25Y4L20!<FT`!BJ5^;FluJx}7OEFLu&^7F`o^n9!~g=4vAFPYk=Hb$Erpb2e5HzU~|*N<+nZb15`-;}7(wPYB?ce~D6KnMhZQ@)`x!?i6~%-YUynN|PguVd|Fgb2WsdgJcs`!^#XNtMCBkEZgb&_+s0$Dm`4R5W^Z%<^do#J^W7?6<N-uVF@OM+<7W*<)8muB0iE#!9-y(goCe9hj~Hox+!;Q6s2w5t3$3`oSQ80nL!4Lk*9x!ye+ZnDnS+>Bw19m|G$rEqG@5u)RX>Va{XHeGNuNV*Idt=Ij&J?+g%mHQiLMB_f@Sa84wo{;}-Alzz(d;w`kTwDl{L?s0{|{s9#Ia5;b3*z-o+ovNQ>qzQTLM0b(&C6503y;1sr1O~2P^xfR~r?cC5>hVuKw=aJB=|7-Hz&`',
    'chip': 'c-pO3O>ZPM5dAN6;W9{ex9zrbLr9zvSA<snC})uthzKlNt@gk3UfJC<Nrv5kaFQNR+pc<5e)W-$r^km}<xOtyPj_xRpYr{ix2HQB&Zql#A0FO5p6))LzB=9g=*-#ShtHGk-5UN$H>Qa>{d7JV>`DHd&UP7_jPX@kGRC;xoAhE#?a?gKSDasrDScZz1eny5(@E_4m>f&T=Hs|=LV=m0p&}Xuu)GAYVKwVv?iag=IAaB(bWk1#WP1H<z4CL#r=@U!=I1Is>BdGQFnsUQFmmW)6aq*$05o_2BJ%XW(tDsd=ero<N@J3H!IC$Y2y&Mq+-<W+N@}MW9w@T%_`*G{E2;<;+wj0Q0AQDu`Y#XwqEFarvWOkiwYLm3IwFBoGmUhHD)i!n*wkH#+I(-E%QSoC8>tvVSLOjVV3VCL#it8u;xLymzr6|57Z{SAQEvbx#BYi{T4NJ+?cUGXsk7#AietCwGQZw)oQ=>BR3=4xnl*GO6I`Ac2=hC_G;Z9dCCa+rb{*H>^3EW0YcfXMH*cTa{Cq+L-xGm_qs&tX$|)5K<jsyVAZwhbOV7_|SPlD$YNnKEFZ#YPBb*=hd$Z3xA~l$ShvLhAEaEce6nEi{w_=aI+wLatdK|-Tx?OQ0+s1T}8UM;enKqMNN~t_T4~|M8)V9YyLl4^<97A&F;)!Huh-z|0$?O<b(W!Rjt0z0~wU$<Tag5}$thEKIt9zs$+I*2#R&rl*p*5OhlB9!?j`{K_M>S}o6g`Dl_nI=LOait^z;XRYIGZaQp3jgBvdWK?*f>)lyo#}dt4=fO^5oqBlg8PeL2<4mk<2}WBQK4vTxKLmOww2mG@_W+<F+BGIYt*oUHix=G#X?{E$~#%pf8*@(=@eoXz|-QT$v1`65W@B@gpI1eu0~#pBd>DPYS=k^60u-L7y#8?LK_*Z+up+e70WS%VGk64qCzJltux9)l&Tc_Vz}uIf~Sc2|QmGOtK*JHpbpU#v<I(Aoke&$_Wwt%o4wy*J}VV`=RcietGcSje}qO<-uQQvqvsbvw0V_`=EDSB{MbU1_nogTQj~jzCw6{+D7e+yjJ!Lbx^$Ot^DV2#PsWN4;M)Pudh|jZx<dO!GuI4l}XK`^k;3C8a1#vnRKe!CoLndU*2I~R1^GuRy!lgn~lN4g<k7!SAeULv5*;C9(KXO>`#VWmDOY$MSCP$ebYu=#iXXDr#8)u=JR~Lsv^GwO9%+?i-)7YKj>&6cGQ7<)Shwn<&%;gUnHbB6G`qhYHHCwCN)RvQlRISq7__=hl>c{r55d3NU;)OR6x6dHlWPV{NqSS7HT}zNYbQ|W|8-BS&i%HkZwNnsC(!vEb4@(*gu~$O>-x6%j+g#q@YSukPufSAoL^TL}CcBOQxFl&kJKwFigjzEhGKeq>*ibq7oL_B0AjeHX1si9zUDF*~~%0Y>G`AOr*NMXw`~Dz-#$h?ZWa(7KsY75CJtpd@Cc5j(3o{VHRmz1Edu-F{{SbZEa|K@n6QM<pEkZJnQJgi3@UOH_)}liWYXIO4DvqcJ6&Rys@YMtW=;ooLa5fKs{0U*tBQof<@mPhC6_)3=IxRp&d?`z0!8%{%vomZ5xfYE%QGNiYv>EiBF&Y23V7&Z~',
    'head': 'c-qxjNzWul5&bVMaqB~6R<3hHT(FQ3GC~{>vT~iVFkpFXOUUwnC$?OwzR#90o-y>HyE3~fGvdYeBI~=y`!7>zpQZZk<BhY=M|%6&yT==SJ|Azt_}7>3-ap=a_xRQ0&0n-To?1VZf9j`yK90kc*3x<KN4HGBp;r@n(>$ByqV<4Zkp{jy`aL^d)Lv-N5<g;kx5rU>#X+s=cyVuRMmF8nwRj~Tlp&%Fs+D7XhP)`0inZ0S{YgTVo=oX^PLfcr_Y;=ybJK!C#oiT4<z+I`|EYI?q7PXNYka*|RTgTj%Lt|>NY+gTH<ussKK=^GgE7>3Jk^QDIM^6`M`XA(0A&F}0zcyxfNEwK8^MOVhE8x+5;yY=g?=gzV6M{5iB*F~`yBM!KbL1Ns|A{peJ&DQWFx7~kXke*eNgFhC`}%yQ0WugwzU#ZGGBHUr2;GZrg&-i^@WX#=F>)C@8>ic34^=2)|;hE_`fCb-w;8CVwRJTa}GoG>0N|J)bm<3H}0uNi(_AZ)E2Fcpgqj_R6+hq@}r8sMioPNs<_)#<dm2>mgjHV)5rF<sm9@#QR2AG=<al%TC<Lgz*>rd*pcO3kzmlh6>gxX&UI)zowRw0V2)nVdVB=NQY?Lv_!9brn^E4$co5@i!OVY;1i@w~^y}4>k2XL(WU<DZ27>lC16nt|hpmn#s3ixB3wd~^cxzp1sMDsJ2F=_KW$`H36!M7P+zb+K$j9FMo^W>HUK`(^zpf9yTz6ymO!7^LBFEj>QCBpj+w|i*N&i+-Fa*<YG0h+PsgLP_L5wHs@uflwBvM|5acP&pZtVQA=C;qA%j{<HBg(?K=pB~<TG{YJs6RoEJk(PysFk=ZRsy|ZxlykD1+RuIL%x2Z0>2x+qF(q)p+wUKpUqjo51UoT6+K<+Ia8QSp0()XHfdT`$8FNCq%bFaZ|8jyouI1gBsl&aF*0e$o&0^HxFxV95~iC$b>^h1Tcl2n%(mIm-OtT7*P&E^#c1G3X@-`?#Eszp{$;74rDO+^7V@BSOBvX}&P*u?S#~kg%fx3+nKBB%nj%jKm#L9?_bCz_aM`B_t8$$pmEvUzC>LsRnPQZ#Q-slNiZbGDN(<2d?VVaSIme=lzKtsU2ZYu}DHRvLZZ(H<8Y@E{9f%K$`iYPDg4Eh+anw%z@K{Od9OED&az68U-;V@J_U2K?&oSPeanG<)rV*x3UwYt#Y2vhy@~O=o=4NghVC~-qcUV((B%&X?>zx0|lrl)Z^i_ey>=;qk7F8J!?uB<OUsv?cbhJ{+6e8V)kfdp@X%O|U=ah<aMd9d1X#a@N8Y}!>$chd~b^%!Q7AW72yy3+4g9OQm3mc(%C;FmPe|Uz-%ee&wG6A(k7a+s3Ns<@jTyA|!XUY==G{d@pi-~E`G85~fFDi<|z-<Y0Qt`%mAo)=DT+GP4*nLsyKfUxPyQl|eG{}RCZmf*vHfANs<bQQ)k2A;Y?c8{FXfu(GvQqP+7*r>9p6xFgqn6s+Y7TVB$moJzq59|1yswNF#pZjnP?<gHwtPK^0ikT`D@B#A9UN`uqcR=;WN)yOMx4@zvhG=E^I&Frh@#{Sf%^b%<T>lO+5S}SR9cZO)8ydf8L+>TI?(cJdeC=pTh9e&m3IugNa><s2rNRq6`j<t)LzZr%k&#*&ofD0*g4y;&3G%fRxZwk!{whe+qrp#22I-mfPPX>{J<7~xIDMaxwsQ6IPH{;7-kZfb8jfez)(LeJv4~xwB-S(ZoW;i#^?Me%>j1P5gTS&EmUaDslo@8xuDDnlA79O=CoF`rKHxp4bUv32cqx9h)YsJv2h$WNQXWU+u~`vA+M}%HVaXI7h|H6kXW$sAu3x(!Zl9?8R+R|<9+M0%TFBT;V;;3WjQ!NkMNieafCX%`CO3D<WUiAcqHd6YgB&d&L}R&Bh&XC=+A(Spa2Y6qlQSl4Iyc-o6FH{ii09Rttg}ipZGZZO0;wmpTVTBX7R0fnGJo8#Rn!lH!sC=r5s}>LWRzqy+YaEF87B<^}rVDalHO<SfLgBSjFJdcnW1R<C_RdEg6O7X`PQ0w?SeH@oi|RV6ym{ZdKfu5|G}*-CeQ*v$gZWMJ5a7R>?@lvdF!fzyOeib1X&&s~MuqIbS-}0Y1UVSj!Qccf*w}y7GapY})nYLI0OSe;Z;57e9uzW=SFAS!DEiTdJ%EQHJ$H4ymDl@kX#d2ar4-Vh@P$Y&Z!q@@s*xcbt+=1Wf&N{Ma^+1OE2m?e=m=HP5Yo<qUqvDAa?8<J4M)WuA=TFwf#frMAvgjKi$_2x?imO45;`6{p(l25!!FOI%~SMUcL@+l>H}YV;9*m?I|?>F>y`@Rf*Od6Fb|7#7t7NiFiCVT+E$KZE>4&d!-Fvb(T^4xg~k*}6FKFF9N0i+~YhazsIdiR;KeHoty}&;M82_~)oQR1=ldM666)0kH1jsdhwbHa4c=;(^Pg?G4HH=489vZrC2%7Nadp;^IUl8yhH;?W<SnHK~y4y_dX^VL!t4Ga$~F4cbE87H2XS`t%=Owqu^*ur4Uu`|YT6aS21XIV@^G2|VyVP!VDD5lw-a7r;J<mb=04VKXxtA4xeDIgHh#4RM-J%YeG;UV#K>fL8^i55=)OUxPfsKO;Kj0Y48S<?%|!{REk|)x?EC(4Bt%w2L<SJ&dRng)1XBK;gdGxaa^Ya3?ZO-{cLJ`fwv*VKOpupt2&rmr_I@Xh&-zHpdC^+gEy%X)Vm`Y96`Z3#2ekNAT5=5@`4ZUSyGK97h&d3(m<5b=sQ6-0a4+>hTKs$KBWa8c;Y$KlT0h{{|EaLSz',
    'body': 'c-pmD*^VSf75$eIh?fGzo{{Y*cwrL=u?PudS+UL_42&2s7|Z|8xl3eLcXgW{7_w_BZ&t=~;w~rdjrr>G{#|L~v(mq~JVbN7lsBKfy*$`-y}bGS%Xe?zUmm`?eCzV?duz<q;uEgs8m<?EEA57_t&Pz$8q}Wlx{YSsjPy1P?`B%<+DMy7wv5^LAoAYIs7A;0b6X?#vNe|M$bK}8oZ4{4?R|{4J98qqe0sfnn;<6OOIPavF#@7*qjEdj6WvBKxsk9J`u4*BC}4+S={expPKVZ!2lrFnmm<qFeKUJCv0GP1^G3#})-9XVwGmp=AZB`gL~EI3@NzBPZr&GOz|lW-Mk3?Wvc7|5`Ed2uplgDDpi!)(M|yw7dsvO$+p9%`Fe5&u1lxFk@1g<JlCGo_Xy)Q4E@u-iOAWraMsPYpoDm;-Wp2#AbZUGZqk2|fjj;|-W@qidh$EAf2Xx0ejMIn73&-u0&bMa|Q)HBKj7+9mvk@GtaCSmt1&wV}G}b!{4nD?$4@Ly?&kq-TjQdP6ntjT}x^mAeqysPe55b0YOp~R+*8*F)F6XeaT*57uHm)@h!YCrd)y9uayR{zqg6G`A@z22tq_N1_EefaC0}h8ns|q3ywZm-Utu`W-gU)K|Fg7_+inD{mpdeN<ja(+VF3g0`6#Ind;D}yyzP_Z=YSqO$kzhC@QpG$hZKNWSJVPQWuk~-v)76?+v*~y$5uEKF&Z#~l3Ox+tk5#u7?c1=+Xxr1D*iDrrqIu#$W*-L@8K2<n&uNF$S4hKY)|fiEJedhog7$<85f&=#n1J7!1_FV3L#*un;Ki2mIVsvO(Rwm|ntMpn4egkw3C_a`d%|<wR@j@n>!gEEjxJ8RDA(LwPdVuOv~<VozI6;clp~1%df%7ab6$Fm(~)DC<+Y`$(gX7dYo#An!+?BI?`_0@E0XQ{^15!0B?4eQG}bG@{K0~04}#fvxK6vxMsyJK=o}4V@UX;$m53N<vQ2PMK%*N_q}Ephw(t_mIDhRr#nxapowx+C)(;6<05pHAL6@=dwrnMkMowuT-7|k$aq31>IQ38Lg`?h>Y3_Fq9ACS7na36ZKim&1!9;E-T{*l#WRE??4Z9W1VL1;dQ6T?_Ap0lU6ew=y4-?k~aifh39H0No!3f%qA35@|<$d#qI{pM5cXQ3RMu=o+8XJw26kdPdy6B$Wl5(Fmw$#CUw)75Sph<uFoLjoJQ;5iW28*(Lkf{3z#I>V9dqcfpn}g?3H+JF}JVIcimvPg~hr4IMJN=gR@iT%Jms={dMX7CWm@X*24m?y@_g?8CNsQx;2ccN}M13Tr(U>17)*b%w1I2m9TX{fxq-6R4%A^tH0RU+(ePFu413~`zb8e|oG4eKMT4FDXFcZGAM5PcG!6<f#+(bmEEiMsTfL$VDrmKi1>sK@pxBSJ6{8PL+$ss<b3^m9+#I`ua=9w22iGP5K0&keB?Q2AW_RFO;_ZZp~`VnkIj`rvoZ`_60Wy${h-BUilqPzKpP_id!!!&aeZak4y?yGSP_a&IWdTyiPf}!u8+x0DAHyk{dH@ef_Y~9qR9SM-6pLspokSi1HY6=5rh9|f*q9}1f81;?qMV{?;rbcD+UlUBb49zg}$#I@EIWxY!=rNpI@&8pMXur7+k9{6n#Q!d4)wCs2_PP@%r;OMJ`A^&8)_K<trHk_uwBHi64bZkjYjwqv25r?bt3)(h%}u7hQHD^MGp+HQ!U^<1KbpOnwlgeEn|fxVNjxC3J))q1mNF1BJPuya7CR`ZklC%&l@N~1OGslSW~h1DqvzU$lTu}4__V~|-8%->q8Cte&bpnOc<pD(x!f`x8JS;&1QPF8cWIIsN0$zdOa!g0^wm<vXej;DTEk0@zxyC18?(2Y+mqCSl7qow8Ob|4S=}4^!cH9$8))YQDfoTo!UzEfOC)4n1frf5Aa)!&hN$f(>3t$p>5L`!6n0p)vN7Q_;x~v`X$&Ku!Xh7S-0^AA)8^L-2#Yox#?mAg*dME-?|hzs)SPlC@wE}`(uP-0UFRI?aa!cD0it#%JMn;$1@zmcA15%+FP!p!lv=c?jrgPi3wwZ@O%2nVLTRUPyplB0&qns3;(?;1kLHWy^W&zJITp`U8KjW)ey5GUNwLya0Rx)#%c-0PGQMt9poR0ExoCtFuw$-@mZqMPx}_T}ltFBZ(a3(zNWdT&omA{5O=Dj9O;fx%H67OCNS&@Mbv9LJJk&W}Rwr_BP96fQQ@bPhQ1=}*D@F@Rj|Y%)`9K>Zm1|HXV|uHY@}1+~-yM5>Z7q@4iW~PTeqEcid;Ohe{{v=6@!^iiTTOJzQSbk#`5%ug`9ES6@}YYGmEz8vRh#Ad8f#$FfX=xh!5YHM(l3L(xPR-G?|u}T{PU++YkTRBn*Zr0gVjQ~QkWwLKsK|JA|kA@=dh739UrTl3YGF#wIy51M|dD$e?BdK;5sZDKbB?x@?0cSyfr;R(iqf8?kiR~l9N*AI<uW#-_j;8k=&ZFVJKV(1my^t`rU1q@dClGO4wN8#~^I%07BT`v`e&`H21G^SQ>A19(sX>bF8!ghQU2v{Gwsr-)#*RIVf)pwMSwAWki>lI&@3u$C-G@ebtCirgvEnJuHzT=f|EhBi$PQCY%^=4!*ev8N!9dmf@@%O1=1n%o{}91_$up?|e^A3@K_p<gUKyXI0*;w2gpBd6qApYDo{vdX=OL4kpK?bQ;9(h!i4XP*N-qhNM>D<-U?IO=?HeDs*R$r0M>#GFyL4*rm4EIBDUur7-Vw)Z<jwaalJbKG3KgR8m_?6H_%UQOZdFoluY{7COPF|3-k5#BLeHpu<9#S&P8N^;!{M&5TTsP5=2+4}l{qVHB!pxj?aiD(B;2Zo0;Oo!>M~2)7ZqjCT0mXaf;`ta$L!lcxLfm@Yg~yOaTxh)K~k)M@B!ja2UVJ=P#=!gtGhKB}pF9nBoYpQM)SBu|c2t>%c(q*hr3>0fv8A_sZo=eUk@m33yGXLyw0+TI?gv}<~cYK>Eja2}g~{q?^A!{eC+',
    'brief_head': 'c-p;JNsrw&4E`@Z`(Q1$q`7r(fi6I|plE|YYjWrzK+pn3kpEsTqGZpTnYIB^0S}L~CGsOheU#rWZ(he-U&Qj~a<`jxi7#KgTJDrvmzTf)_4?JD<?ikB(Q@~zGHz9NRc77ReO)#jrM0lhu&uQ^wAfN@dskF#2R!K7(V9M5Rjj3!@x3EOHx%#@4hIuyy6Mh%cu<Tet$-H#6j)%lt@h<$HEw%rhajrk@_b!BmS8jnqcE66mTE~mI-h<(rpPKR?J}5YBAWs+$^05lYx5y<G+^6hEkH{rIiKc)>9?pZ*X$KR{^Y^@YoBW^k(0dFzB(c>0PKyniINp5D+oQgnH|aZ+(1mKf9&0L9cG;U`UL6K-Ctz)R<I=6W90@;4Cd2E^53V7Jiua*mC~5Lbk6_CCqRrNpJn88+j1)p<QW4DBE!EW`wIW!^c&T7#)FVQL&zE+t9vCwWpWi2kAat6oy5Mk_r!l()+eaxt)4`J`8mQ=$EvnlnB^i(TQ|OD9xl?;E1r-L*cS-Q`g`@OT!OkthuY3HQ}m^tGVM4YVV|A)7xk-nFZ#Q#!Md_Zp?Iv{V`|->IWk!oSgPM9PNzATFCVO5p}^xkWEuBmi^IL2%^@S?uK+S|yS)JZuRk>OwN#k8iT$QvKa_YnDSezpg82=?+@;<GCU+boN0#>AvsSq|6%as+6{qS}GHD5^&b3fTb4YQyS=KZhJ^Zl-&-VlVy5^8=cF{~LwQizeJBw5E#HXSe!U`G&^X-H67CX05&6ty%huj-5$uUs*vkZ;Viwq#E78zW|Aw%&Pk+CHgk#*(zjJ**I8SHYsefPw9@BM0=v8?8KPXvFQO*;7F+`@TIr}GZaPyH%G6qk3Gb@5`;BG4MxU*bM~?N@};cJlgO@^9|5YR&FUn1~$|4J`{Tk1GJP)JgGUT1GU}fScB;8HMi{dpD4&HsoePg&?M>DT@Lz7QQ|FAl*x!c0=Lip<?r<{j8O*4sc0={m~g~Dsu)6UW*`YUJ1?O{2X@Db*z&q;oX6{8~hAxZDKj3DP!Uf2;9-t>_Yj0@HmG2qwvgx{1{In7vTL5DWRWeE$;s>86p34drW%*Y0E#1T!rSHT=D|84M^#sO`ywhkR)S4*$5njU6dgIEQMi4mZL-mx9;7_PNqi0m3mzTjGWk%@8(7dwD2~kZQSVTp1*ga_!+Q`?|{f$!^#eIH@_aBYGz+YingZ~U*^5y83y3Os{9C`=O=VB0Adg9z3@u>!q|yy6_9;X6oX|(+>zvVTwF1XjJ`ueLll$e$GaO}EJ%?cX+Whc(=a@@=%_a6+?A8ZJtH;OdD68KF>nu^h7$k=DlWH(N%tJka^%!9dSBuMQ*4-kUv77BeDEYpecuz_NyD2mQp8(h`__1lk^xp~3&O3Z?*gnXHEvwehu%xU0Dk*JZ^~j60WPg!)er=nprzf8ayypi@810l`#TXu',
    'brief': 'c-pmDYp)zR5&bVCBt9^U{BHa5iI;dtNJxN$1glm1(Fw3XMA(I8wf~(uRpsu!cV<EY!I?W<p7!Ios(f7Ke0_QQW^LoMwSReeispJ*Uw!ua@?_KX^6K-i-n@Q$dHVYDt;^HztT9(hpKvwTaJ?8RsTeLx8>44xP<twM8O^vY;%yk-ZE3b^BP}A?b!@!^kxN@gH9DT(mN{}?m&TGE*^fper#75%rH|2yGY5jpr`OB338D{Ie+9ls_-G)SdL+{$-hYRe5P1oPnj~35SdEt0A4zu8LJJBZclvVg?r{`MeWj^Mvw&u=mav5_(#Nd9Hg50<HAsNu2$*%(i^puvCMp&UzB@;7IzrqceelYhOyhLv#@8{br|JEuG1lQ>8o=qK=#e4iLAs6%dGldoThQZ>j<-h-v&tyzJ~9+BX9FCoa0<{^L1Wuy(arVFf+Ig*!3QG(eCWdkA7j~4jHal4SXb`8LOS8a!WcF=hH0`Ca<KqSse)i`SuSvQna{N*LKv$EaklYe(Qd6rE{D4?9Dff^fW{(gcU3sO?r_+-T2&Bvs2#TE<(EkNEldZi!`S3RDb5ad=XF?<G4i@$e~_7I`-pwQJvgElov%-6ZMEuRok(OjBT}V#SX!VWNS+}<%5(jT^C+!(HJgs765zx;aI`-uxD3{)1D117Rd^#Nz`9Hy1zIFaIHx+%k~VLq%aC@87>Y*TxCb;#q%vv{IQgD-;xyK>W$!bl=}iDkGt~wy5tPKnN@LqlgPTwfh%$8<27D;M6iy*uE<7^V0cRSkJc6@29-_w7u>%<nhO@$+v`baO;0ktg@U{>u??#%YrM&A23t(>cfS0xsl60eX%<O>kG+79EuFGU0b5jm>`rh8fNf)KQoAQzpzmKImUiaBg?br=!a_?ozJ?CNP<j%43brY%Uco3ViTj8zVRvC~BdM_gqwTFl;-RCCgW?v!!JUpvc!2H34X?MO`c({%OY5_aNJUY9dcwv|#TvNn=$rix@exYuJBDFpnu!X0%j^o#^Q!I_lrW3E~%RdA(Ptg2XgRZE5v3HJ~(z=1%+z^V3V32jl_@+>0w3C^(a;l7TrJtLXX{AW(aicq-%F0AD3Qelhxs2VH^q~CFgzTPalK{g7Wv!_U>@ih=ZR1c9*l)^bH4&rOT`niN9&H@0>=@G>a|JbxVgSq^KQKB9EV9T!5Doz5p{OOQA*tB+>84XeyN|GWK>G=xg&U(o%Yt8xUIsZAEMmnn?PT<&Iy34cqe~@AI3z~*6sC|b>_#`VFQ-3|P}JygsiR>I%kknGMVmjJMn7wF8YO?2I17mjf+vbI@_#uPp#AI_d+lM@yFcjobLv>kHJ^<TvAZ!gHPWE-{hv!0-7^;<Ms8zCoz7mn_D-h(CjA8z8K>=4ku#`i+p-Le8vGbksWNz}s3c)edQ!!5OhZ4RkB}ub<_cKU(H~d9pqbuEh1&OJR_HLoh*BZf!dzNmBBlx;|MDSyuHGEn7N0Yo^5C|MZSG^6DQr+TK!nCj8oYhSPP!)o+OO^%K%9H@;@PkJ66lm14AdJvfsYuK+q6ASlPEdQx(&JV9-K{SWg3VIl&-NSPMkn<u_Bhq;5*Cz8ZhnDAj8bZHt;xpwoKn%j>d2t(f?Nw(0+5fvCFoz$p0>8)wIRF^?E`lr<<k?5NTWD(m5IkYZtEqwBOz_?hN+9X-?wk!ju>h5=9By=qIl)IRM;~2I_J|CTZ+PBjpE4;|GglewB^J5B|aE>p;f!vs)ekFxMIXS;<+KJ$LXDvlkyE1>;TXw&ev)gJ=hf>qy>Nh!PpHD6wef2E7Ge3MV?`sXfyoI_s()866P|QvcdcQR54tN@vQZdI}WQn#yV+FP6}WTw5Ab_;Uz-zLLhBJ}q*n-BwQ#=%OywgjdURb@XC6H4728LsU++V5c^`nr_}Lu*d948`~&qcenr#D2&?AOW$uj?k^kxG^I{h6!L`F2n*ZSZA}f+n?h-au)mTc*KZB>K=j=Z;g05435drj7uXlioDw84^}c}L+e}S#{lrIp@`3ZnGf++{&_uXoP6EjZ*dJ$xim5j_2GdCk>i{j$Xs{nSV8!rsuy06S`Iq<q#uTp(O^3NSsMD=eolVslcXf`(>ZEvvH)&vXYIoYZlsN7ABaIf4ru&K71cZH@ei2Im(`&_)Zyf*j>DcRQYYAQ}ZrrQ*b#2n_{hyfq4>UUka&Diz)r4D%dixK}|0vDF)h^dhtQZN|Pda5n@Be2b#cLF-VdOvUvCMzeg0LB$fkFs+dK|*FSzH)FJ8bm2RgN1;J7LSxFViu~{fUM7>Box6KYyu(+8+Hw^FN<LAk9%L2!xJd%EAg%9LdflhXq!0d;xQqN-|TmgTyHxp#orkIeclywfju`SU&UDdmMqC-1M$VceipxpDe%}F|Q@&4eaLiEzVith}MK>!^)9lsK?F8oAU<d1rl@XQ9vvF7)Jq}EpimR>-=e_5bkestr|}{4}B#KXUgM)UK4SThhG@x?aiTMDGcO8r}hYLQLc4~Nl6czzTa?%+-D?D%JeSleS`(w2B_8}IMGAr@4~k6h)n$8m_k@~wUnq?+$5RDUljLx<grW*U)=bfTv}n*e8^LM({EK7x#EB#iso6qe5oZ3je3<kIC3z#Sj9yRzXK^m+Jkb@OoSoVQN;LiuS21v#+9S>nY?E;%0EuG8#*EPTG$e$b3n8*?{vzVEG9r+vPJrkMlF$jBqXhvR832!fQ6b_v&pMzd>C4ClGrVSpxzc{9&%OOI2T#PS2H8iJG+0r)I;E%m1q>CM4Tg7f+{!Z6!qyE%gnNy=HAN)oQFC3UT`!CKUS)E>51vS+NTRI)Gm=YLOhNtfuDT?*IrP$<M*@%SrdJ?ELqHqrt7@=i8F9Y^OBA4&M1kI=#w<5i4GwB>t??Uy&5qHJ@)K(2Hbg@X=&CtS*I<-KbziC!o<N#IA5^;{tIX9>6U%|AIf&zjO^v|={Mi}8@!;H3;',
    'footer': 'c-pO2%Z}Vc6#W-(*mzO59xm7H5JHhyAz%klR4-?c5*RTADMa~q&bejxboWdviiF$ly6(Eqb05{8rpJd|`<vYUneJSgr~LNK{d6a8p5DIu_;CL?-F=$AneKkIakjIY4W7w$*KD0$&(j@tAZ6z`%e+83nbVaMIlcu)a<drTDvd3-9egSGo$9tON-WhZMJfCs-IBix^sVIIcs25Svb11AQ|2|BvML2`TK*1}#mJ>;n_6$HG9@d%R%1%0kW?p|+kJ7HJfmduM`UHVSG=)3J8=bCPMT@@`w{f2wrRMk+uKs3IU>7U$G*9_A20X{jl9zM(hKn=+2eDiiK%&r274<$2bEP6P!Yht#}}%x4e{B9aS1hNukrl=)6pQ|XNI>;Ga0_{y(05V3*Fngn%H_$g+IOoSO>riT$b(z5H((`3u=aZ)!zngUuop0y&%%1mA1+dcR*_J`+h~(ng;fL9m(*lOWjIkC#1z)Ds)SGKaZf&8A`EsMrGD&>Au?qSl#?Z>AbZR1{qSXd#0qWr@oT5AP!(?d`42rNXjoTw}vxwc@&FgeQCRN_&*4m%dCMFDT^~JVKOMTmPW10kq$H^`nlGgQIMAH4&(%t1<*2(N0m}n9rYAXx@_q{)8LU7d_VVLf8!n}208bxYr~^>K54XyFBe~1iPdxrms(X@tg3rC-UNHLk+YZBsJdSVYx4+}wlVZn&~;>9FLB3IV-yh}kUv{>a~m_$Ke_2!qY_ghK<Sn1OAm$bpT)R0_0<w;ug+{)OfH6#3lVbf#zNJ<(=WEglWJ>5QG$4OQ{>%CBDZgfyk`>%{Ff7!bT%W8=zuL_;$tmI9pgX;dJt9&V)-&j8-E-ioh<mTgG06a`7GxsaA?q+qU%S_H__UW&F=4GKQrfS2vJ=Rhb{#Q%7j4|xJ{oDYLiZJ7&8<hTAnjih{)JqP_|Z6airvYrIEj2#K$?D0oxWRaL^Kt+PM0n+~alkVJt(Chpw$wdQ=lGwKlriwy<C<NeyOwI`jTM$~r-dhn9p0FqzTjNe}Du2gkNqd#2ont7I{FwBqe$^sdFx9a_&guBheX5yJtn{uhWvlLKqGUDE<dJj=S({}rj0aR}<s?%Ei%9Lce-2dw{I!DHFs1NN*(>st4ruQNbT(WYa4*~mJk^KTzmq9a2VA3-rpezS3U{rU5Mz`IFb',
}

STYLES = {}


def _load_styles():
    for name, blob in GLYPH_BLOBS.items():
        raw = zlib.decompress(base64.b85decode(blob.encode()))
        data = json.loads(raw.decode())
        glyphs = {}
        for ch, (adv, w, h, dx, dy, hexdata) in data["glyphs"].items():
            glyphs[ch] = (adv, w, h, dx, dy, bytes.fromhex(hexdata))
        STYLES[name] = (data["space_adv"], data["ag_h"], glyphs)


# ---------------------------------------------------------------------------
# The day's news — Tuesday, 24 November 2026 (frozen data)
# ---------------------------------------------------------------------------
DATE_LINE = "Tuesday, November 24, 2026  ·  The day's biggest stories, summed up in a single image"

LEAD = {
    "kicker": "CLIMATE  ·  ANTALYA  ·  TOP STORY",
    "headline": "Blame Game as COP31 Climate Talks Collapse",
    "body": (
        "Blame flew on Monday after the COP31 climate talks in Antalya "
        "collapsed without a final agreement — the first such failure "
        "since Copenhagen in 2009. The EU rejected a closing deal with "
        "no mention of fossil fuels, and Australia's opposition "
        "demanded chair Chris Bowen resign."
    ),
    "chips": ["First failure since Copenhagen 2009", "Record overtime in Antalya", "Pacific nations 'let down'"],
}

STORIES = [
    {
        "kicker": "RUSSIA–UKRAINE WAR  ·  LIBYA",
        "headline": "Ukraine Sinks Russian Corvette",
        "body": (
            "Zelenskyy confirmed Monday that Ukrainian sea drones sank "
            "Russia's corvette Merkury at Benghazi, 2,400 km from the "
            "front line. Seven drones struck Sunday, also hitting the "
            "Angara cargo ship; 10 people were wounded."
        ),
    },
    {
        "kicker": "MIDDLE EAST  ·  GAZA",
        "headline": "Israeli Strikes Kill UN Aid Worker",
        "body": (
            "Israeli strikes killed at least three people in Gaza on "
            "Monday, including UNRWA worker Adel al-Helo, hit at a "
            "water well in Jabalia. Three colleagues were wounded; "
            "UNRWA says 397 of its staff have now been killed."
        ),
    },
    {
        "kicker": "BUSINESS  ·  MARKETS",
        "headline": "Nvidia Soars 30% as Huang Returns",
        "body": (
            "Nvidia's board unanimously reinstated co-founder Jensen "
            "Huang as chief executive on Monday, 11 days after he "
            "resigned. Shares leapt over 30%, adding $900 billion in "
            "market value in a broad tech rally."
        ),
    },
    {
        "kicker": "CAUCASUS  ·  DIPLOMACY",
        "headline": "Armenia Unveils Peace Charter",
        "body": (
            "Armenia published a draft constitution dropping the "
            "reference Baku calls a territorial claim over Karabakh. "
            "Pashinyan staked his credibility on the plan: adoption "
            "would bring the peace treaty's signing."
        ),
    },
]

BRIEFS = [
    ("CHINA", "An official surnamed Ma is sentenced to death for spying: 100+ reports passed to a foreign agency, 35 of them state secrets, for over $150,000."),
    ("IRAN", "Tehran vows to use 'all our tools' against the US naval blockade, calling it military aggression; Hormuz could reopen 'within hours' if the US meets its terms."),
    ("BANGLADESH", "Dhaka says ex-PM Sheikh Hasina, who faces a death sentence at home, will be arrested and jailed if she returns from India in December."),
    ("MERCURY", "ESA–JAXA's BepiColombo is safely in Mercury orbit after an 8-year journey, despite a software glitch that cut its capture burn short; its two orbiters separate on Dec 9."),
    ("GENEVA", "The youngest world title match in chess history opens today: champion Gukesh, 20, faces challenger Sindarov, 20, over 14 games for $2.5 million."),
]

FOOTER = "Compiled from the day's reports: Reuters · Associated Press · Al Jazeera · The Guardian · ESA"

# ---------------------------------------------------------------------------
# Canvas drawing
# ---------------------------------------------------------------------------
canvas = bytearray(bytes(PAPER) * (W * H))


def rect(x0, y0, x1, y1, color):
    """Filled rectangle, inclusive bounds, clipped to the canvas."""
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W - 1, x1)
    y1 = min(H - 1, y1)
    if x1 < x0 or y1 < y0:
        return
    row = bytes(color) * (x1 - x0 + 1)
    for yy in range(y0, y1 + 1):
        off = (yy * W + x0) * 3
        canvas[off:off + len(row)] = row


def rounded_rect(x0, y0, x1, y1, radius, color):
    """Filled rectangle with rounded corners, inclusive bounds."""
    height = y1 - y0 + 1
    for t in range(height):
        d = min(t, height - 1 - t)
        if d < radius:
            inset = radius - int((radius * radius - (radius - d) ** 2) ** 0.5 + 0.5)
        else:
            inset = 0
        rect(x0 + inset, y0 + t, x1 - inset, y0 + t, color)


def hline(x0, x1, y, color, width=1):
    rect(x0, y, x1, y + width - 1, color)


def vline(x, y0, y1, color, width=1):
    rect(x, y0, x + width - 1, y1, color)


def blit(px, py, w, h, packed, color):
    """Blend one glyph's 4-bit coverage bitmap onto the canvas."""
    fr, fg, fb = color
    idx = 0
    for yy in range(h):
        cy = py + yy
        if cy < 0 or cy >= H:
            idx += w
            continue
        base = cy * W * 3
        for xx in range(w):
            byte = packed[idx >> 1]
            cov = (byte >> 4) if (idx & 1) == 0 else (byte & 15)
            idx += 1
            if cov:
                cx = px + xx
                if 0 <= cx < W:
                    off = base + cx * 3
                    if cov == 15:
                        canvas[off] = fr
                        canvas[off + 1] = fg
                        canvas[off + 2] = fb
                    else:
                        inv = 15 - cov
                        canvas[off] = (fr * cov + canvas[off] * inv) // 15
                        canvas[off + 1] = (fg * cov + canvas[off + 1] * inv) // 15
                        canvas[off + 2] = (fb * cov + canvas[off + 2] * inv) // 15


def measure(text, style):
    """Text width in tenths of a pixel, from the glyph advances."""
    space_adv, _ag_h, glyphs = STYLES[style]
    total = 0
    for ch in text:
        if ch == " ":
            total += space_adv
        else:
            g = glyphs.get(ch)
            total += g[0] if g else space_adv
    return total


def text(x, y, s, style, color):
    """Draw a string with its ascender line at y; returns end x (pixels)."""
    space_adv, _ag_h, glyphs = STYLES[style]
    pen = x * 10
    for ch in s:
        if ch == " ":
            pen += space_adv
            continue
        g = glyphs.get(ch)
        if g is None:
            pen += space_adv
            continue
        adv, w, h, dx, dy, packed = g
        if w:
            blit((pen + 5) // 10 + dx, y + dy, w, h, packed, color)
        pen += adv
    return (pen + 5) // 10


def wrap(s, style, max_width_px):
    """Greedy word wrap; returns lines fitting max_width_px."""
    limit = max_width_px * 10
    lines, current = [], ""
    for word in s.split():
        trial = word if not current else current + " " + word
        if measure(trial, style) <= limit:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_block(x, y, s, style, color, max_width, line_gap=6):
    """Draw wrapped text; returns the y just below the block."""
    _space_adv, ag_h, _glyphs = STYLES[style]
    line_h = ag_h + line_gap
    for line in wrap(s, style, max_width):
        text(x, y, line, style, color)
        y += line_h
    return y


def centered(y, s, style, color):
    w = measure(s, style)
    text((W * 10 - w) // 20, y, s, style, color)
    return y + STYLES[style][1]


# ---------------------------------------------------------------------------
# Compose the front page
# ---------------------------------------------------------------------------


def build():
    # Outer frame
    rect(14, 14, W - 15, 15, LIGHT_RULE)
    rect(14, H - 16, W - 15, H - 15, LIGHT_RULE)
    rect(14, 14, 15, H - 15, LIGHT_RULE)
    rect(W - 16, 14, W - 15, H - 15, LIGHT_RULE)

    x0, x1 = MARGIN, W - MARGIN
    y = 36

    # Masthead
    y = centered(y, "O N E - P A G E   W O R L D   B R I E F I N G", "top_kicker", ACCENT) + 8
    y = centered(y, "THE WORLD TODAY", "masthead", INK) + 6
    y = centered(y, DATE_LINE, "date_line", MUTED) + 10
    hline(x0, x1, y, RULE, 3)
    hline(x0, x1, y + 4, RULE, 1)
    y += 18

    # Lead story
    text(x0, y, LEAD["kicker"], "kicker", ACCENT)
    y += 24
    y = text_block(x0, y, LEAD["headline"], "lead_head", INK, CONTENT_W, line_gap=8) + 6
    y = text_block(x0, y, LEAD["body"], "lead_body", BODY_INK, CONTENT_W, line_gap=9) + 10

    # Lead stat chips, drawn as rounded pills
    cx = x0
    for chip in LEAD["chips"]:
        tw = (measure(chip, "chip") + 5) // 10
        rounded_rect(cx, y, cx + tw + 28, y + 34, 8, CHIP_BG)
        text(cx + 14, y + 7, chip, "chip", CHIP_INK)
        cx += tw + 44
    y += 44

    hline(x0, x1, y, LIGHT_RULE, 2)
    y += 16

    # 2 x 2 story grid
    col_gap = 36
    col_w = (CONTENT_W - col_gap) // 2
    grid_top = y
    for row in range(2):
        col_x = [x0, x0 + col_w + col_gap]
        max_bottom = grid_top
        for col in range(2):
            s = STORIES[row * 2 + col]
            sy = grid_top
            text(col_x[col], sy, s["kicker"], "kicker", ACCENT)
            sy += 23
            sy = text_block(col_x[col], sy, s["headline"], "head", INK, col_w, line_gap=5) + 4
            sy = text_block(col_x[col], sy, s["body"], "body", BODY_INK, col_w, line_gap=6)
            max_bottom = max(max_bottom, sy)
        # vertical divider between the two columns
        vline(x0 + col_w + col_gap // 2, grid_top + 2, max_bottom - 4, LIGHT_RULE, 1)
        grid_top = max_bottom + 12
        if row == 0:
            hline(x0, x1, grid_top - 10, LIGHT_RULE, 1)
    y = grid_top + 2

    hline(x0, x1, y, RULE, 2)
    y += 10

    # In brief
    text(x0, y, "AROUND THE WORLD — IN BRIEF", "brief_head", INK)
    y += 26
    for place, line in BRIEFS:
        label = place + "  —  "
        lw = (measure(label, "brief_head") + 5) // 10
        text(x0, y, label, "brief_head", ACCENT)
        y = text_block(x0 + lw, y, line, "brief", BODY_INK, CONTENT_W - lw, line_gap=4) + 4

    # Footer pinned near the foot of the page
    y = max(y + 8, H - 92)
    hline(x0, x1, y, RULE, 1)
    y += 12
    centered(y, FOOTER, "footer", MUTED)


# ---------------------------------------------------------------------------
# PNG encoding (zlib, filter 0) and entry point
# ---------------------------------------------------------------------------


def encode_png():
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    stride = W * 3
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += canvas[yy * stride:(yy + 1) * stride]
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))


def main():
    _load_styles()
    build()
    out = os.environ.get("ENTRY_OUT")
    if not out:
        base = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
        out = os.path.join(base, "entry.png")
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out, "wb") as f:
        f.write(encode_png())


if __name__ == "__main__":
    main()
