      MODULE TEST_MOD
      
      real:: strain_inc, lambda_temp
	  real:: EE_new, EE_old, SS_inc, sig_inc
      
      END MODULE
C
C User subroutine VUMAT
      subroutine vumat (
C Read only -
     *     nblock, ndir, nshr, nstatev, nfieldv, nprops, lanneal,
     *     stepTime, totalTime, dt, cmname, coordMp, charLength,
     *     props, density, strainInc, relSpinInc,
     *     tempOld, stretchOld, defgradOld, fieldOld,
     *     stressOld, stateOld, enerInternOld, enerInelasOld,
     *     tempNew, stretchNew, defgradNew, fieldNew,
C Write only -
     *     stressNew, stateNew, enerInternNew, enerInelasNew )
	  USE TEST_MOD
C     
      include 'vaba_param.inc'
C
      dimension coordMp(nblock,*), charLength(nblock), props(nprops),
     1     density(nblock), strainInc(nblock,ndir+nshr),
     2     relSpinInc(nblock,nshr), tempOld(nblock),
     3     stretchOld(nblock,ndir+nshr), 
     4     defgradOld(nblock,ndir+nshr+nshr),
     5     fieldOld(nblock,nfieldv), stressOld(nblock,ndir+nshr),
     6     stateOld(nblock,nstatev), enerInternOld(nblock),
     7     enerInelasOld(nblock), tempNew(nblock),
     8     stretchNew(nblock,ndir+nshr),
     9     defgradNew(nblock,ndir+nshr+nshr),
     1     fieldNew(nblock,nfieldv),
     2     stressNew(nblock,ndir+nshr), stateNew(nblock,nstatev),
     3     enerInternNew(nblock), enerInelasNew(nblock)
C     
      dimension a0(2), a1(2), a1_a1(2,2), ff(2,2), fft(2,2)
      dimension dii2(2,2), bb(2,2), cc(2,2), dnn(2)
      
      character*80 CMNAME
	  
c	  WRITE(*,*) CMNAME
	  
	  IF (CMNAME(1:6).EQ.'MAT_TV') THEN
c		  write(*,*) 'Going to TV', CMNAME
		  CALL VUMAT_TV(
     *     nblock, ndir, nshr, nstatev, nfieldv, nprops, lanneal,
     *     stepTime, totalTime, dt, cmname, coordMp, charLength,
     *     props, density, strainInc, relSpinInc,
     *     tempOld, stretchOld, defgradOld, fieldOld,
     *     stressOld, stateOld, enerInternOld, enerInelasOld,
     *     tempNew, stretchNew, defgradNew, fieldNew,
     *     stressNew, stateNew, enerInternNew, enerInelasNew )
	 
	  ELSEIF (CMNAME(1:6).EQ.'MAT_CH') THEN
c	      write(*,*) 'Going to CH', CMNAME
		  CALL VUMAT_CH(
     *     nblock, ndir, nshr, nstatev, nfieldv, nprops, lanneal,
     *     stepTime, totalTime, dt, cmname, coordMp, charLength,
     *     props, density, strainInc, relSpinInc,
     *     tempOld, stretchOld, defgradOld, fieldOld,
     *     stressOld, stateOld, enerInternOld, enerInelasOld,
     *     tempNew, stretchNew, defgradNew, fieldNew,
     *     stressNew, stateNew, enerInternNew, enerInelasNew )
	  ENDIF
c
	  RETURN
c
	  END
	  
      subroutine vumat_TV(
C Read only -
     *     nblock, ndir, nshr, nstatev, nfieldv, nprops, lanneal,
     *     stepTime, totalTime, dt, cmname, coordMp, charLength,
     *     props, density, strainInc, relSpinInc,
     *     tempOld, stretchOld, defgradOld, fieldOld,
     *     stressOld, stateOld, enerInternOld, enerInelasOld,
     *     tempNew, stretchNew, defgradNew, fieldNew,
C Write only -
     *     stressNew, stateNew, enerInternNew, enerInelasNew )
	  USE TEST_MOD
C     
      include 'vaba_param.inc'	  
C
      dimension coordMp(nblock,*), charLength(nblock), props(nprops),
     1     density(nblock), strainInc(nblock,ndir+nshr),
     2     relSpinInc(nblock,nshr), tempOld(nblock),
     3     stretchOld(nblock,ndir+nshr), 
     4     defgradOld(nblock,ndir+nshr+nshr),
     5     fieldOld(nblock,nfieldv), stressOld(nblock,ndir+nshr),
     6     stateOld(nblock,nstatev), enerInternOld(nblock),
     7     enerInelasOld(nblock), tempNew(nblock),
     8     stretchNew(nblock,ndir+nshr),
     9     defgradNew(nblock,ndir+nshr+nshr),
     1     fieldNew(nblock,nfieldv),
     2     stressNew(nblock,ndir+nshr), stateNew(nblock,nstatev),
     3     enerInternNew(nblock), enerInelasNew(nblock)
C     
      dimension a0(2), a1(2), a1_a1(2,2), ff(2,2), fft(2,2)
      dimension dii2(2,2), bb(2,2), cc(2,2), dnn(2)
      
      character*80 cmname

            
      a0(1) = 1.d0
      a0(2) = 0.d0
      aaal = a0(1)**2 + a0(2)**2      
      a0(1) = a0(1)/sqrt(aaal)
      a0(2) = a0(2)/sqrt(aaal)
      
      dii2(1,1) = 1.d0
      dii2(2,2) = 1.d0
      dii2(1,2) = 0.d0
      dii2(2,1) = 0.d0
      
      dmmu = props(1)
      c0 = props(2)
      c1 = props(3)
      dslope = props(4)
      dintersec = props(5)
      dthreshold = props(6)
      
            
      do ii = 1, nblock                    
      
            
            ff(1,1) = stretchNew(ii,1)
            ff(2,2) = stretchNew(ii,2)
            ff(1,2) = stretchNew(ii,4)
            ff(2,1) = stretchNew(ii,4)
            
            fft(1,1) = ff(1,1)
            fft(1,2) = ff(2,1)
            fft(2,1) = ff(1,2)
            fft(2,2) = ff(2,2)
            
            bb(1,1) = ff(1,1) * fft(1,1) + ff(1,2) * fft(2,1)
            bb(1,2) = ff(1,1) * fft(1,2) + ff(1,2) * fft(2,2)
            bb(2,1) = ff(2,1) * fft(1,1) + ff(2,2) * fft(2,1)
            bb(2,2) = ff(2,1) * fft(1,2) + ff(2,2) * fft(2,2)

            cc(1,1) = fft(1,1) * ff(1,1) + fft(1,2) * ff(2,1)
            cc(1,2) = fft(1,1) * ff(1,2) + fft(1,2) * ff(2,2)
            cc(2,1) = fft(2,1) * ff(1,1) + fft(2,2) * ff(2,1)
            cc(2,2) = fft(2,1) * ff(1,2) + fft(2,2) * ff(2,2)
            
            cc33 = 1.d0/(cc(1,1)*cc(2,2)-cc(1,2)**2)
            
            di1 = cc(1,1)+cc(2,2)+cc33
            
            di4 = cc(1,1)*a0(1)**2 + (cc(1,2)+cc(2,1))*a0(1)*a0(2) +
     &            cc(2,2)*a0(2)**2
            
            a1(1) = ff(1,1)*a0(1) + ff(1,2)*a0(2)
            a1(2) = ff(2,1)*a0(1) + ff(2,2)*a0(2)
            
            a1_a1(1,1) = a1(1)*a1(1)
            a1_a1(1,2) = a1(1)*a1(2)
            a1_a1(2,1) = a1(2)*a1(1)
            a1_a1(2,2) = a1(2)*a1(2)
            
            if(di4 <= 1.d0) then
                di4 = 1.d0
            endif
            
            di1_3 = di1 - 3.d0
            di4_1 = di4 - 1.d0            
            
            if (di1_3 .le. dthreshold) then
                w1 = dmmu + c0*c1*di1_3*exp(c1*di1_3**2)
            else
                w1 = dmmu + dslope * di1_3 + dintersec
            endif

c            sig = 2.d0*w1*bb + 2.d0*w4*a1_a1 - 2.d0*w1*cc33*dii2
            
            stressNew(ii,1) = 2.d0*w1*bb(1,1) - 2.d0*w1*cc33*dii2(1,1)
            stressNew(ii,2) = 2.d0*w1*bb(2,2) - 2.d0*w1*cc33*dii2(2,2)
            stressNew(ii,3) = 0.d0
            stressNew(ii,4) = 2.d0*w1*bb(1,2) - 2.d0*w1*cc33*dii2(1,2)
            
            
            if (stepTime > 0.d0) then
                stressPower = 0.5d0 * (
     *        ( stressOld(ii,1) + stressNew(ii,1) ) * strainInc(ii,1) +
     *        ( stressOld(ii,2) + stressNew(ii,2) ) * strainInc(ii,2) +
     *        ( stressOld(ii,3) + stressNew(ii,3) ) * strainInc(ii,3) )+
     *        ( stressOld(ii,4) + stressNew(ii,4) ) * strainInc(ii,4)
                enerInternNew(ii) = enerInternOld(ii) + 
     &                             stressPower / density(ii)
            endif
            
c            !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            stateNew(ii,1) = defgradNew(ii,1) ! F11
            stateNew(ii,2) = defgradNew(ii,2) ! F22
            stateNew(ii,3) = defgradNew(ii,4) ! F12
            stateNew(ii,4) = defgradNew(ii,5) ! F21
c            
            stateNew(ii,5) = stretchNew(ii,1) ! U11
            stateNew(ii,6) = stretchNew(ii,2) ! U22
            stateNew(ii,7) = stretchNew(ii,4) ! U12
c            
            stateNew(ii,8) = stressNew(ii,1) ! S11
            stateNew(ii,9) = stressNew(ii,2) ! S22
            stateNew(ii,10) = stressNew(ii,4) ! S12
            
c			stateNew(ii,11)=stretchNew(ii,1)*stretchNew(ii,2)-stretchNew(ii,4)**2
			    
        enddo

      
      return
      
      end   

      subroutine vumat_CH(
C Read only -
     *     nblock, ndir, nshr, nstatev, nfieldv, nprops, lanneal,
     *     stepTime, totalTime, dt, cmname, coordMp, charLength,
     *     props, density, strainInc, relSpinInc,
     *     tempOld, stretchOld, defgradOld, fieldOld,
     *     stressOld, stateOld, enerInternOld, enerInelasOld,
     *     tempNew, stretchNew, defgradNew, fieldNew,
C Write only -
     *     stressNew, stateNew, enerInternNew, enerInelasNew )
	  USE TEST_MOD
C     
      include 'vaba_param.inc'	  
C
      dimension coordMp(nblock,*), charLength(nblock), props(nprops),
     1     density(nblock), strainInc(nblock,ndir+nshr),
     2     relSpinInc(nblock,nshr), tempOld(nblock),
     3     stretchOld(nblock,ndir+nshr), 
     4     defgradOld(nblock,ndir+nshr+nshr),
     5     fieldOld(nblock,nfieldv), stressOld(nblock,ndir+nshr),
     6     stateOld(nblock,nstatev), enerInternOld(nblock),
     7     enerInelasOld(nblock), tempNew(nblock),
     8     stretchNew(nblock,ndir+nshr),
     9     defgradNew(nblock,ndir+nshr+nshr),
     1     fieldNew(nblock,nfieldv),
     2     stressNew(nblock,ndir+nshr), stateNew(nblock,nstatev),
     3     enerInternNew(nblock), enerInelasNew(nblock)
C     
      dimension a0(2), a1(2), a1_a1(2,2), ff(2,2), fft(2,2)
      dimension dii2(2,2), bb(2,2), cc(2,2), dnn(2)
      
      character*80 cmname
	  
      a0(1) = 1.d0
      a0(2) = 0.d0
      aaal = a0(1)**2 + a0(2)**2      
      a0(1) = a0(1)/sqrt(aaal)
      a0(2) = a0(2)/sqrt(aaal)
      
      dii2(1,1) = 1.d0
      dii2(2,2) = 1.d0
      dii2(1,2) = 0.d0
      dii2(2,1) = 0.d0
      
	  lam = props(7)
	  mu = props(8)
	  
      do ii = 1, nblock                  
	  
            lambda_temp = stretchNew(ii,1)
			
			EE_new = 0.5 * (lambda_temp**2 - 1)
			
			SS_inc = (lam + 2*mu) * (EE_new)
			
			sig_inc = lambda_temp * SS_inc * lambda_temp
			
			stressNew(ii,1) = sig_inc
			
c            !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            stateNew(ii,1) = defgradNew(ii,1) ! F11
            stateNew(ii,2) = defgradNew(ii,2) ! F22
            stateNew(ii,3) = defgradNew(ii,4) ! F12
            stateNew(ii,4) = defgradNew(ii,5) ! F21
c            
            stateNew(ii,5) = stretchNew(ii,1) ! U11
            stateNew(ii,6) = stretchNew(ii,2) ! U22
            stateNew(ii,7) = stretchNew(ii,4) ! U12
c            
            stateNew(ii,8) = stressNew(ii,1) ! S11
            stateNew(ii,9) = stressNew(ii,2) ! S22
            stateNew(ii,10) = stressNew(ii,4) ! S12
            
c			stateNew(ii,11)=stretchNew(ii,1)*stretchNew(ii,2)-stretchNew(ii,4)**2
			    
        enddo

      
      return
      
      end      