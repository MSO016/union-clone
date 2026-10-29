// program: _security_crypto.cp313-win_amd64.pyd

// ==== FUN_180001010 @ 180001010 ====

/* WARNING: Removing unreachable block (ram,0x0001800015c5) */
/* WARNING: Removing unreachable block (ram,0x0001800015c9) */
/* WARNING: Removing unreachable block (ram,0x0001800015cf) */
/* WARNING: Removing unreachable block (ram,0x000180001c7f) */
/* WARNING: Removing unreachable block (ram,0x000180001c84) */
/* WARNING: Removing unreachable block (ram,0x000180001c8a) */
/* WARNING: Removing unreachable block (ram,0x000180001cd5) */
/* WARNING: Removing unreachable block (ram,0x000180001cdd) */
/* WARNING: Removing unreachable block (ram,0x000180001ce7) */

undefined * FUN_180001010(undefined8 param_1,undefined *param_2)

{
  undefined *puVar1;
  uint uVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  code *pcVar6;
  int *piVar7;
  longlong lVar8;
  longlong *plVar9;
  longlong *plVar10;
  longlong *plVar11;
  ulonglong uVar13;
  code *pcVar14;
  code *pcVar15;
  uint uVar16;
  undefined8 *puVar17;
  code *pcVar18;
  undefined *puVar19;
  undefined *unaff_RSI;
  code *pcVar20;
  undefined *puVar21;
  code *pcVar22;
  longlong *local_res10;
  code *local_res18;
  longlong *local_res20;
  longlong *local_f8;
  longlong *local_f0;
  longlong *local_e8;
  code *local_d8;
  code *local_d0;
  longlong *local_c8;
  code *local_c0 [2];
  longlong *local_b0;
  undefined8 local_a8;
  code *local_a0;
  undefined8 local_98;
  code *local_90 [3];
  longlong *local_78;
  longlong *local_70;
  undefined8 local_68;
  code *local_60 [4];
  undefined8 uVar12;
  
  pcVar20 = (code *)0x0;
  local_e8 = (longlong *)0x0;
  local_res20 = (longlong *)0x0;
  local_res18 = (code *)0x0;
  local_f0 = (longlong *)0x0;
  local_f8 = (longlong *)0x0;
  pcVar6 = (code *)FUN_18000a140((longlong)DAT_180016908);
  if (pcVar6 == (code *)0x0) {
    iVar5 = 0x10;
    puVar21 = PTR_s__security_crypto_py_180011d38;
  }
  else {
    uVar2 = (uint)(pcVar6 == _Py_TrueStruct_exref);
    local_d0 = (code *)param_2;
    if ((pcVar6 != _Py_NoneStruct_exref && pcVar6 != _Py_FalseStruct_exref) && uVar2 == 0) {
      uVar2 = PyObject_IsTrue(pcVar6);
      local_d0 = (code *)param_2;
    }
    pcVar14 = pcVar20;
    if ((int)uVar2 < 0) {
      iVar5 = 0x10;
      pcVar15 = pcVar20;
      puVar21 = PTR_s__security_crypto_py_180011d38;
LAB_180001c32:
      if ((-1 < *(int *)pcVar6) &&
         (*(longlong *)pcVar6 = *(longlong *)pcVar6 + -1, *(longlong *)pcVar6 == 0)) {
        _Py_Dealloc(pcVar6);
      }
    }
    else {
      param_2 = local_d0;
      if ((-1 < *(int *)pcVar6) &&
         (*(longlong *)pcVar6 = *(longlong *)pcVar6 + -1, *(longlong *)pcVar6 == 0)) {
        _Py_Dealloc(pcVar6);
        param_2 = local_d0;
      }
      if (uVar2 != 0) {
        piVar7 = FUN_18000a140((longlong)DAT_180016908);
        if (piVar7 != (int *)0x0) {
          return unaff_RSI;
        }
        iVar5 = 0x11;
        puVar21 = PTR_s__security_crypto_py_180011d38;
        goto LAB_180001dfc;
      }
      lVar8 = PyThreadState_GetUnchecked();
      puVar17 = *(undefined8 **)(lVar8 + 0x78);
      do {
        local_d0 = (code *)*puVar17;
        if ((local_d0 != (code *)0x0) && (local_d0 != _Py_NoneStruct_exref)) break;
        puVar17 = (undefined8 *)puVar17[1];
      } while (puVar17 != (undefined8 *)0x0);
      if ((local_d0 == (code *)0x0) || (local_d0 == _Py_NoneStruct_exref)) {
        local_d0 = (code *)0x0;
        local_d8 = (code *)0x0;
        local_c8 = (longlong *)0x0;
      }
      else {
        if (*(int *)local_d0 + 1 != 0) {
          *(int *)local_d0 = *(int *)local_d0 + 1;
        }
        local_d8 = *(code **)(local_d0 + 8);
        if (*(int *)local_d8 + 1 != 0) {
          *(int *)local_d8 = *(int *)local_d8 + 1;
        }
        local_c8 = (longlong *)PyException_GetTraceback(local_d0);
      }
      plVar9 = (longlong *)FUN_18000a140(DAT_180016ad0);
      if (plVar9 == (longlong *)0x0) {
        iVar5 = 0x13;
        puVar21 = PTR_s__security_crypto_py_180011d38;
        goto LAB_180001609;
      }
      if (*(code **)(plVar9[1] + 0x90) == (code *)0x0) {
        plVar10 = (longlong *)PyObject_GetAttr(plVar9,DAT_180016aa8);
      }
      else {
        plVar10 = (longlong *)(**(code **)(plVar9[1] + 0x90))();
      }
      if (plVar10 != (longlong *)0x0) {
        if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
          _Py_Dealloc(plVar9);
        }
        pcVar15 = (code *)0x1;
        pcVar6 = pcVar20;
        plVar11 = plVar10;
        if ((code *)plVar10[1] == PyMethod_Type_exref) {
          pcVar6 = (code *)plVar10[3];
          plVar11 = (longlong *)plVar10[2];
          if (*(int *)pcVar6 + 1 != 0) {
            *(int *)pcVar6 = *(int *)pcVar6 + 1;
          }
          iVar5 = (int)*plVar11 + 1;
          if (iVar5 != 0) {
            *(int *)plVar11 = iVar5;
          }
          pcVar15 = pcVar20;
          if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
            _Py_Dealloc(plVar10);
          }
        }
        local_90[1] = (code *)0x0;
        local_90[0] = pcVar6;
        plVar9 = (longlong *)
                 FUN_18000a310((longlong)plVar11,local_90 + (longlong)pcVar15,
                               1U - (longlong)pcVar15 | -(longlong)pcVar15 << 0x3f,0);
        if (((pcVar6 != (code *)0x0) && (-1 < *(int *)pcVar6)) &&
           (*(longlong *)pcVar6 = *(longlong *)pcVar6 + -1, *(longlong *)pcVar6 == 0)) {
          _Py_Dealloc(pcVar6);
        }
        if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
          _Py_Dealloc(plVar11);
        }
        if (plVar9 == (longlong *)0x0) {
          iVar5 = 0x13;
          puVar21 = PTR_s__security_crypto_py_180011d38;
          goto LAB_180001609;
        }
        plVar10 = (longlong *)FUN_18000a140(DAT_180016b60);
        local_e8 = plVar9;
        if (plVar10 == (longlong *)0x0) {
          iVar5 = 0x14;
          puVar21 = PTR_s__security_crypto_py_180011d38;
          goto LAB_180001609;
        }
        if (*(code **)(plVar10[1] + 0x90) == (code *)0x0) {
          plVar11 = (longlong *)PyObject_GetAttr(plVar10,DAT_180016a00);
        }
        else {
          plVar11 = (longlong *)(**(code **)(plVar10[1] + 0x90))();
        }
        puVar21 = PTR_s__security_crypto_py_180011d38;
        if (plVar11 == (longlong *)0x0) {
          local_res18 = (code *)0x0;
          iVar5 = 0x14;
          local_res20 = (longlong *)0x0;
          if (-1 < (int)*plVar10) {
            *plVar10 = *plVar10 + -1;
            local_res18 = (code *)0x0;
            local_res20 = (longlong *)0x0;
            if (*plVar10 == 0) {
              _Py_Dealloc(plVar10);
              local_res18 = (code *)0x0;
              local_res20 = (longlong *)0x0;
            }
          }
          goto LAB_180001609;
        }
        if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
          _Py_Dealloc(plVar10);
        }
        pcVar15 = (code *)0x1;
        plVar10 = plVar11;
        pcVar6 = pcVar20;
        if ((code *)plVar11[1] == PyMethod_Type_exref) {
          pcVar6 = (code *)plVar11[3];
          plVar10 = (longlong *)plVar11[2];
          if (*(int *)pcVar6 + 1 != 0) {
            *(int *)pcVar6 = *(int *)pcVar6 + 1;
          }
          iVar5 = (int)*plVar10 + 1;
          if (iVar5 != 0) {
            *(int *)plVar10 = iVar5;
          }
          pcVar15 = pcVar20;
          if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
            _Py_Dealloc(plVar11);
          }
        }
        local_c0[1] = (code *)0x0;
        local_c0[0] = pcVar6;
        pcVar15 = (code *)FUN_18000a310((longlong)plVar10,local_c0 + (longlong)pcVar15,
                                        1U - (longlong)pcVar15 | -(longlong)pcVar15 << 0x3f,0);
        if (((pcVar6 != (code *)0x0) && (-1 < *(int *)pcVar6)) &&
           (*(longlong *)pcVar6 = *(longlong *)pcVar6 + -1, *(longlong *)pcVar6 == 0)) {
          _Py_Dealloc(pcVar6);
        }
        if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
          _Py_Dealloc(plVar10);
        }
        if (pcVar15 == (code *)0x0) {
          iVar5 = 0x14;
          puVar21 = PTR_s__security_crypto_py_180011d38;
          goto LAB_180001609;
        }
        pcVar6 = (code *)PyNumber_ToBase(pcVar15,0x10);
        if (pcVar6 == (code *)0x0) {
          iVar5 = 0x14;
LAB_1800018ba:
          plVar9 = (longlong *)0x0;
          pcVar6 = pcVar20;
LAB_1800018c1:
          puVar21 = PTR_s__security_crypto_py_180011d38;
          if ((-1 < *(int *)pcVar15) &&
             (*(longlong *)pcVar15 = *(longlong *)pcVar15 + -1, *(longlong *)pcVar15 == 0)) {
            _Py_Dealloc(pcVar15);
          }
LAB_1800015d5:
          if (plVar9 != (longlong *)0x0) goto LAB_1800015da;
          goto LAB_1800015ee;
        }
        if ((-1 < *(int *)pcVar15) &&
           (*(longlong *)pcVar15 = *(longlong *)pcVar15 + -1, *(longlong *)pcVar15 == 0)) {
          _Py_Dealloc(pcVar15);
        }
        pcVar15 = (code *)plVar9[1];
        local_res18 = pcVar6;
        if (pcVar15 == PyUnicode_Type_exref) {
          iVar5 = (int)*plVar9 + 1;
          if (iVar5 != 0) {
            *(int *)plVar9 = iVar5;
          }
        }
        else {
          if (pcVar15 == PyLong_Type_exref) {
            plVar9 = (longlong *)(**(code **)(PyLong_Type_exref + 0x58))(plVar9);
          }
          else if (pcVar15 == PyFloat_Type_exref) {
            plVar9 = (longlong *)(**(code **)(PyFloat_Type_exref + 0x58))(plVar9);
          }
          else {
            plVar9 = (longlong *)PyObject_Format(plVar9,DAT_180016758);
          }
          if (plVar9 == (longlong *)0x0) {
            iVar5 = 0x15;
            puVar21 = PTR_s__security_crypto_py_180011d38;
            goto LAB_180001609;
          }
        }
        pcVar15 = pcVar6;
        if (pcVar6 == _Py_NoneStruct_exref) {
          pcVar15 = DAT_1800168c0;
        }
        if (*(int *)pcVar15 + 1 != 0) {
          *(int *)pcVar15 = *(int *)pcVar15 + 1;
        }
        local_a8 = DAT_1800168b8;
        uVar2 = 0x7f;
        local_98 = DAT_180016900;
        if ((*(uint *)(plVar9 + 4) & 0x40) == 0) {
          uVar3 = *(uint *)(plVar9 + 4) & 0x1c;
          if (uVar3 == 4) {
            uVar16 = 0xff;
          }
          else {
            uVar16 = 0x10ffff;
            if (uVar3 == 8) {
              uVar16 = 0xffff;
            }
          }
        }
        else {
          uVar16 = 0x7f;
        }
        if ((*(uint *)(pcVar15 + 0x20) & 0x40) == 0) {
          uVar3 = *(uint *)(pcVar15 + 0x20) & 0x1c;
          if (uVar3 == 4) {
            uVar2 = 0xff;
          }
          else {
            uVar2 = 0x10ffff;
            if (uVar3 == 8) {
              uVar2 = 0xffff;
            }
          }
        }
        local_b0 = plVar9;
        local_a0 = pcVar15;
        pcVar6 = (code *)FUN_18000a440((longlong)&local_b0,0xffff,
                                       plVar9[2] + *(longlong *)(pcVar15 + 0x10) + 0x13,
                                       uVar2 | uVar16);
        if (pcVar6 == (code *)0x0) {
          iVar5 = 0x15;
          local_res20 = (longlong *)0x0;
          puVar21 = PTR_s__security_crypto_py_180011d38;
          if (pcVar15 != (code *)0x0) goto LAB_1800018c1;
          goto LAB_1800015d5;
        }
        if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
          _Py_Dealloc(plVar9);
        }
        if ((-1 < *(int *)pcVar15) &&
           (*(longlong *)pcVar15 = *(longlong *)pcVar15 + -1, *(longlong *)pcVar15 == 0)) {
          _Py_Dealloc(pcVar15);
        }
        plVar9 = (longlong *)PyUnicode_AsEncodedString(pcVar6,0,0);
        if (plVar9 == (longlong *)0x0) {
          iVar5 = 0x15;
          puVar21 = PTR_s__security_crypto_py_180011d38;
          goto LAB_1800015f3;
        }
        if ((-1 < *(int *)pcVar6) &&
           (*(longlong *)pcVar6 = *(longlong *)pcVar6 + -1, *(longlong *)pcVar6 == 0)) {
          _Py_Dealloc(pcVar6);
        }
        plVar10 = (longlong *)FUN_18000a140(DAT_180016a08);
        local_res20 = plVar9;
        if (plVar10 == (longlong *)0x0) {
          iVar5 = 0x16;
          puVar21 = PTR_s__security_crypto_py_180011d38;
          goto LAB_180001609;
        }
        if (*(code **)(plVar10[1] + 0x90) == (code *)0x0) {
          plVar11 = (longlong *)PyObject_GetAttr(plVar10,DAT_180016b20);
        }
        else {
          plVar11 = (longlong *)(**(code **)(plVar10[1] + 0x90))();
        }
        puVar21 = PTR_s__security_crypto_py_180011d38;
        if (plVar11 == (longlong *)0x0) {
          iVar5 = 0x16;
          if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
            _Py_Dealloc(plVar10);
          }
          goto LAB_180001609;
        }
        if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
          _Py_Dealloc(plVar10);
        }
        pcVar15 = (code *)0x1;
        plVar10 = plVar11;
        pcVar6 = pcVar20;
        if ((code *)plVar11[1] == PyMethod_Type_exref) {
          pcVar6 = (code *)plVar11[3];
          plVar10 = (longlong *)plVar11[2];
          if (*(int *)pcVar6 + 1 != 0) {
            *(int *)pcVar6 = *(int *)pcVar6 + 1;
          }
          iVar5 = (int)*plVar10 + 1;
          if (iVar5 != 0) {
            *(int *)plVar10 = iVar5;
          }
          pcVar15 = pcVar20;
          if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
            _Py_Dealloc(plVar11);
          }
        }
        local_90[2] = pcVar6;
        local_78 = plVar9;
        plVar9 = (longlong *)
                 FUN_18000a310((longlong)plVar10,local_90 + (longlong)(pcVar15 + 2),
                               2U - (longlong)pcVar15 | -(longlong)pcVar15 << 0x3f,0);
        if (((pcVar6 != (code *)0x0) && (-1 < *(int *)pcVar6)) &&
           (*(longlong *)pcVar6 = *(longlong *)pcVar6 + -1, *(longlong *)pcVar6 == 0)) {
          _Py_Dealloc(pcVar6);
        }
        if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
          _Py_Dealloc(plVar10);
        }
        if (plVar9 == (longlong *)0x0) {
          iVar5 = 0x16;
          puVar21 = PTR_s__security_crypto_py_180011d38;
          goto LAB_180001609;
        }
        iVar5 = (int)*plVar9 + 1;
        if (iVar5 != 0) {
          *(int *)plVar9 = iVar5;
        }
        local_68 = 0;
        local_70 = plVar9;
        pcVar15 = (code *)PyObject_VectorcallMethod(DAT_1800169b0,&local_70,0x8000000000000001,0);
        if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
          _Py_Dealloc(plVar9);
        }
        if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
          _Py_Dealloc(plVar9);
        }
        if (pcVar15 == (code *)0x0) {
          iVar5 = 0x16;
          puVar21 = PTR_s__security_crypto_py_180011d38;
          goto LAB_180001609;
        }
        param_2 = DAT_180016908;
        iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016908,pcVar15);
        if (iVar5 < 0) {
          iVar5 = 0x16;
          goto LAB_1800018ba;
        }
        if ((-1 < *(int *)pcVar15) &&
           (*(longlong *)pcVar15 = *(longlong *)pcVar15 + -1, *(longlong *)pcVar15 == 0)) {
          _Py_Dealloc(pcVar15);
        }
        pcVar6 = local_d0;
        if (((local_d8 != (code *)0x0) && (-1 < *(int *)local_d8)) &&
           (*(longlong *)local_d8 = *(longlong *)local_d8 + -1, *(longlong *)local_d8 == 0)) {
          _Py_Dealloc();
        }
LAB_180001db1:
        if (((pcVar6 != (code *)0x0) && (-1 < *(int *)pcVar6)) &&
           (*(longlong *)pcVar6 = *(longlong *)pcVar6 + -1, *(longlong *)pcVar6 == 0)) {
          _Py_Dealloc();
        }
        if (((local_c8 != (longlong *)0x0) && (-1 < (int)*local_c8)) &&
           (*local_c8 = *local_c8 + -1, *local_c8 == 0)) {
          _Py_Dealloc();
        }
        piVar7 = FUN_18000a140((longlong)DAT_180016908);
        if (piVar7 != (int *)0x0) goto LAB_180001e13;
        iVar5 = 0x19;
        puVar21 = PTR_s__security_crypto_py_180011d38;
        goto LAB_180001dfc;
      }
      iVar5 = 0x13;
      pcVar6 = (code *)0x0;
      puVar21 = PTR_s__security_crypto_py_180011d38;
LAB_1800015da:
      if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
        _Py_Dealloc(plVar9);
      }
LAB_1800015ee:
      if (pcVar6 != (code *)0x0) {
LAB_1800015f3:
        if ((-1 < *(int *)pcVar6) &&
           (*(longlong *)pcVar6 = *(longlong *)pcVar6 + -1, *(longlong *)pcVar6 == 0)) {
          _Py_Dealloc(pcVar6);
        }
      }
LAB_180001609:
      pcVar15 = (code *)0x0;
      puVar19 = *(undefined **)PyExc_Exception_exref;
      pcVar6 = pcVar15;
      if (*(longlong *)(lVar8 + 0x70) == 0) {
        local_f0 = (longlong *)0x0;
      }
      else {
        puVar1 = *(undefined **)(*(longlong *)(lVar8 + 0x70) + 8);
        if (puVar1 != puVar19) {
          if ((*(uint *)(*(longlong *)(puVar19 + 8) + 0xa8) & 0x4000000) == 0) {
            uVar13 = FUN_18000d500(puVar1,puVar19);
            iVar4 = (int)uVar13;
          }
          else {
            uVar12 = FUN_180009f30(puVar1,(longlong)puVar19);
            iVar4 = (int)uVar12;
          }
          local_f0 = (longlong *)0x0;
          if (iVar4 == 0) goto LAB_180001bab;
        }
        FUN_18000d220("_security_crypto._machine_key",puVar19,iVar5,puVar21);
        local_f0 = *(longlong **)(lVar8 + 0x70);
        *(undefined8 *)(lVar8 + 0x70) = 0;
        pcVar6 = pcVar20;
        if (local_f0 != (longlong *)0x0) {
          pcVar6 = (code *)local_f0[1];
          if (*(int *)pcVar6 + 1 != 0) {
            *(int *)pcVar6 = *(int *)pcVar6 + 1;
          }
          pcVar14 = (code *)PyException_GetTraceback(local_f0);
          if ((pcVar14 != (code *)0x0) && (*(int *)pcVar14 + 1 != 0)) {
            *(int *)pcVar14 = *(int *)pcVar14 + 1;
          }
          if (*(int *)pcVar6 + 1 != 0) {
            *(int *)pcVar6 = *(int *)pcVar6 + 1;
          }
          iVar5 = (int)*local_f0 + 1;
          if (iVar5 != 0) {
            *(int *)local_f0 = iVar5;
          }
        }
        plVar9 = (longlong *)**(undefined8 **)(lVar8 + 0x78);
        **(undefined8 **)(lVar8 + 0x78) = local_f0;
        if (((pcVar6 != (code *)0x0) && (-1 < *(int *)pcVar6)) &&
           (*(longlong *)pcVar6 = *(longlong *)pcVar6 + -1, *(longlong *)pcVar6 == 0)) {
          _Py_Dealloc(pcVar6);
        }
        if (((pcVar14 != (code *)0x0) && (-1 < *(int *)pcVar14)) &&
           (*(longlong *)pcVar14 = *(longlong *)pcVar14 + -1, *(longlong *)pcVar14 == 0)) {
          _Py_Dealloc(pcVar14);
        }
        if (((plVar9 != (longlong *)0x0) && (-1 < (int)*plVar9)) &&
           (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
          _Py_Dealloc(plVar9);
        }
        local_f8 = (longlong *)FUN_18000a140(DAT_180016a08);
        if (local_f8 != (longlong *)0x0) {
          if (*(code **)(local_f8[1] + 0x90) == (code *)0x0) {
            plVar9 = (longlong *)PyObject_GetAttr(local_f8,DAT_180016b20);
          }
          else {
            plVar9 = (longlong *)(**(code **)(local_f8[1] + 0x90))();
          }
          if (plVar9 == (longlong *)0x0) {
            iVar5 = 0x18;
            puVar21 = PTR_s__security_crypto_py_180011d38;
            goto LAB_180001bab;
          }
          if ((-1 < (int)*local_f8) && (*local_f8 = *local_f8 + -1, *local_f8 == 0)) {
            _Py_Dealloc();
          }
          local_f8 = (longlong *)0x0;
          if ((code *)plVar9[1] == PyMethod_Type_exref) {
            pcVar22 = (code *)plVar9[3];
            local_res10 = (longlong *)plVar9[2];
            if (*(int *)pcVar22 + 1 != 0) {
              *(int *)pcVar22 = *(int *)pcVar22 + 1;
            }
            iVar5 = (int)*local_res10 + 1;
            if (iVar5 != 0) {
              *(int *)local_res10 = iVar5;
            }
            pcVar18 = pcVar20;
            if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
              _Py_Dealloc(plVar9);
            }
          }
          else {
            pcVar18 = (code *)0x1;
            pcVar22 = pcVar20;
            local_res10 = plVar9;
          }
          local_60[1] = (code *)DAT_180016c18;
          local_60[0] = pcVar22;
          plVar9 = (longlong *)
                   FUN_18000a310((longlong)local_res10,local_60 + (longlong)pcVar18,
                                 2U - (longlong)pcVar18 | -(longlong)pcVar18 << 0x3f,0);
          if (((pcVar22 != (code *)0x0) && (-1 < *(int *)pcVar22)) &&
             (*(longlong *)pcVar22 = *(longlong *)pcVar22 + -1, *(longlong *)pcVar22 == 0)) {
            _Py_Dealloc(pcVar22);
          }
          if ((-1 < (int)*local_res10) && (*local_res10 = *local_res10 + -1, *local_res10 == 0)) {
            _Py_Dealloc();
          }
          if (plVar9 != (longlong *)0x0) {
            iVar5 = (int)*plVar9 + 1;
            if (iVar5 != 0) {
              *(int *)plVar9 = iVar5;
            }
            local_a8 = 0;
            local_b0 = plVar9;
            pcVar15 = (code *)PyObject_VectorcallMethod
                                        (DAT_1800169b0,&local_b0,0x8000000000000001,0);
            if (-1 < (int)*plVar9) {
              *plVar9 = *plVar9 + -1;
              if (*plVar9 == 0) {
                _Py_Dealloc(plVar9);
              }
              if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
                _Py_Dealloc(plVar9);
              }
            }
            if ((pcVar15 != (code *)0x0) &&
               (iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016908,pcVar15), -1 < iVar5)) {
              if ((-1 < *(int *)pcVar15) &&
                 (*(longlong *)pcVar15 = *(longlong *)pcVar15 + -1, *(longlong *)pcVar15 == 0)) {
                _Py_Dealloc(pcVar15);
              }
              if (((pcVar6 != (code *)0x0) && (-1 < *(int *)pcVar6)) &&
                 (*(longlong *)pcVar6 = *(longlong *)pcVar6 + -1, *(longlong *)pcVar6 == 0)) {
                _Py_Dealloc(pcVar6);
              }
              if (((local_f0 != (longlong *)0x0) && (-1 < (int)*local_f0)) &&
                 (*local_f0 = *local_f0 + -1, *local_f0 == 0)) {
                _Py_Dealloc(local_f0);
              }
              if (((pcVar14 != (code *)0x0) && (-1 < *(int *)pcVar14)) &&
                 (*(longlong *)pcVar14 = *(longlong *)pcVar14 + -1, *(longlong *)pcVar14 == 0)) {
                _Py_Dealloc(pcVar14);
              }
              plVar9 = (longlong *)**(undefined8 **)(lVar8 + 0x78);
              **(undefined8 **)(lVar8 + 0x78) = local_d0;
              pcVar6 = local_d8;
              param_2 = local_d0;
              if (((plVar9 != (longlong *)0x0) && (-1 < (int)*plVar9)) &&
                 (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
                _Py_Dealloc();
                param_2 = local_d0;
              }
              goto LAB_180001db1;
            }
          }
        }
        iVar5 = 0x18;
        puVar21 = PTR_s__security_crypto_py_180011d38;
      }
LAB_180001bab:
      plVar9 = (longlong *)**(undefined8 **)(lVar8 + 0x78);
      **(undefined8 **)(lVar8 + 0x78) = local_d0;
      if (((plVar9 != (longlong *)0x0) && (-1 < (int)*plVar9)) &&
         (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
        _Py_Dealloc();
      }
      if (((local_d8 != (code *)0x0) && (-1 < *(int *)local_d8)) &&
         (*(longlong *)local_d8 = *(longlong *)local_d8 + -1, *(longlong *)local_d8 == 0)) {
        _Py_Dealloc();
      }
      if (((local_c8 != (longlong *)0x0) && (-1 < (int)*local_c8)) &&
         (*local_c8 = *local_c8 + -1, *local_c8 == 0)) {
        _Py_Dealloc();
      }
      if (pcVar6 != (code *)0x0) goto LAB_180001c32;
    }
    param_2 = local_d0;
    if (((local_f0 != (longlong *)0x0) && (-1 < (int)*local_f0)) &&
       (*local_f0 = *local_f0 + -1, *local_f0 == 0)) {
      _Py_Dealloc();
      param_2 = local_d0;
    }
    if (((pcVar14 != (code *)0x0) && (-1 < *(int *)pcVar14)) &&
       (*(longlong *)pcVar14 = *(longlong *)pcVar14 + -1, *(longlong *)pcVar14 == 0)) {
      _Py_Dealloc(pcVar14);
    }
    if (((pcVar15 != (code *)0x0) && (-1 < *(int *)pcVar15)) &&
       (*(longlong *)pcVar15 = *(longlong *)pcVar15 + -1, *(longlong *)pcVar15 == 0)) {
      _Py_Dealloc(pcVar15);
    }
    if (((local_f8 != (longlong *)0x0) && (-1 < (int)*local_f8)) &&
       (*local_f8 = *local_f8 + -1, *local_f8 == 0)) {
      _Py_Dealloc();
    }
  }
LAB_180001dfc:
  FUN_18000d220("_security_crypto._machine_key",param_2,iVar5,puVar21);
LAB_180001e13:
  if (((local_e8 != (longlong *)0x0) && (-1 < (int)*local_e8)) &&
     (*local_e8 = *local_e8 + -1, *local_e8 == 0)) {
    _Py_Dealloc();
  }
  if (((local_res18 != (code *)0x0) && (-1 < *(int *)local_res18)) &&
     (*(longlong *)local_res18 = *(longlong *)local_res18 + -1, *(longlong *)local_res18 == 0)) {
    _Py_Dealloc();
  }
  if (((local_res20 != (longlong *)0x0) && (-1 < (int)*local_res20)) &&
     (*local_res20 = *local_res20 + -1, *local_res20 == 0)) {
    _Py_Dealloc(local_res20);
  }
  return unaff_RSI;
}



// ==== FUN_180001e80 @ 180001e80 ====

undefined * FUN_180001e80(undefined8 param_1,char *param_2,longlong param_3,longlong param_4)

{
  int iVar1;
  longlong lVar2;
  undefined *puVar3;
  longlong *plVar4;
  longlong *local_res10;
  undefined *local_18;
  undefined8 local_10;
  
  local_res10 = (longlong *)0x0;
  local_18 = &DAT_180016978;
  local_10 = 0;
  if (param_4 == 0) {
LAB_180001f91:
    if (param_3 == 1) {
      plVar4 = *(longlong **)param_2;
      iVar1 = (int)*plVar4 + 1;
      if (iVar1 != 0) {
        *(int *)plVar4 = iVar1;
      }
      goto LAB_18000201b;
    }
LAB_180001f97:
    param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                 "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","encrypt_blob",
                 "exactly",1,&DAT_180010bad,param_3);
    plVar4 = (longlong *)0x0;
  }
  else {
    lVar2 = *(longlong *)(param_4 + 0x10);
    plVar4 = (longlong *)0x0;
    if (lVar2 < 0) goto LAB_180001fd6;
    if (lVar2 < 1) goto LAB_180001f91;
    if (param_3 != 0) {
      if (param_3 != 1) goto LAB_180001f97;
      local_res10 = *(longlong **)param_2;
      iVar1 = (int)*local_res10 + 1;
      if (iVar1 != 0) {
        *(int *)local_res10 = iVar1;
      }
    }
    param_2 = param_2 + param_3 * 8;
    lVar2 = FUN_18000ac00(param_4,(undefined8 *)param_2,(longlong *)&local_18,param_4,
                          (longlong)&local_res10,param_3,lVar2,"encrypt_blob");
    plVar4 = local_res10;
    if (-1 < (int)lVar2) {
      for (; param_3 < 1; param_3 = param_3 + 1) {
        if ((&local_res10)[param_3] == (longlong *)0x0) {
          param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
          PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                       "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","encrypt_blob",
                       "exactly",1,&DAT_180010bad,param_3);
          plVar4 = local_res10;
          goto LAB_180001fd6;
        }
      }
LAB_18000201b:
      puVar3 = FUN_1800026b0(param_1,(undefined *)plVar4);
      if (plVar4 == (longlong *)0x0) {
        return puVar3;
      }
      if ((int)*plVar4 < 0) {
        return puVar3;
      }
      *plVar4 = *plVar4 + -1;
      if (*plVar4 != 0) {
        return puVar3;
      }
      _Py_Dealloc(plVar4);
      return puVar3;
    }
  }
LAB_180001fd6:
  puVar3 = PTR_s__security_crypto_py_180011d38;
  if (((plVar4 != (longlong *)0x0) && (-1 < (int)*plVar4)) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)
     ) {
    _Py_Dealloc(plVar4);
  }
  FUN_18000d220("_security_crypto.encrypt_blob",param_2,0x1c,puVar3);
  return (undefined *)0x0;
}



// ==== FUN_180002060 @ 180002060 ====

longlong FUN_180002060(int *param_1,int *param_2)

{
  int *piVar1;
  int *piVar2;
  int *piVar3;
  int *piVar4;
  code *pcVar5;
  longlong lVar6;
  longlong lVar7;
  
  lVar7 = DAT_180016788;
  if (DAT_180016cf0 < 1 || *(longlong *)(DAT_180016788 + 0x20) != 0x50) {
    lVar7 = 0;
    pcVar5 = (code *)(**(code **)(DAT_180016788 + 0x130))();
    if (pcVar5 != (code *)0x0) goto LAB_1800020ff;
  }
  else {
    DAT_180016cf0 = DAT_180016cf0 + -1;
    pcVar5 = *(code **)(&DAT_180016cb0 + (longlong)DAT_180016cf0 * 8);
    *(longlong *)pcVar5 = 0;
    *(longlong *)(pcVar5 + 8) = 0;
    *(longlong *)(pcVar5 + 0x10) = 0;
    *(longlong *)(pcVar5 + 0x18) = 0;
    *(longlong *)(pcVar5 + 0x20) = 0;
    *(longlong *)(pcVar5 + 0x28) = 0;
    *(longlong *)(pcVar5 + 0x30) = 0;
    *(longlong *)(pcVar5 + 0x38) = 0;
    *(longlong *)(pcVar5 + 0x40) = 0;
    *(longlong *)(pcVar5 + 0x48) = 0;
    PyObject_Init(pcVar5);
    PyObject_GC_Track(pcVar5);
LAB_1800020ff:
    if (pcVar5 != (code *)0x0) {
      *(int **)(pcVar5 + 0x10) = param_1;
      if (*param_1 + 1 != 0) {
        *param_1 = *param_1 + 1;
      }
      *(int **)(pcVar5 + 0x18) = param_2;
      if (*param_2 + 1 != 0) {
        *param_2 = *param_2 + 1;
      }
      piVar4 = DAT_180016b00;
      piVar3 = DAT_1800169f0;
      piVar2 = DAT_1800169c8;
      piVar1 = DAT_180016858;
      lVar6 = _PyObject_GC_New(DAT_180016da8);
      if (lVar6 != 0) {
        *(code **)(lVar6 + 0x18) = pcVar5;
        *(code **)(lVar6 + 0x10) = FUN_180002260;
        if (*(int *)pcVar5 + 1 != 0) {
          *(int *)pcVar5 = *(int *)pcVar5 + 1;
        }
        *(undefined1 *)(lVar6 + 0x74) = 0;
        *(undefined4 *)(lVar6 + 0x70) = 0;
        *(undefined8 *)(lVar6 + 0x30) = 0;
        *(undefined8 *)(lVar6 + 0x38) = 0;
        *(undefined8 *)(lVar6 + 0x40) = 0;
        *(undefined8 *)(lVar6 + 0x20) = 0;
        *(undefined8 *)(lVar6 + 0x28) = 0;
        if ((piVar2 != (int *)0x0) && (*piVar2 + 1 != 0)) {
          *piVar2 = *piVar2 + 1;
        }
        *(int **)(lVar6 + 0x50) = piVar2;
        if ((piVar3 != (int *)0x0) && (*piVar3 + 1 != 0)) {
          *piVar3 = *piVar3 + 1;
        }
        *(int **)(lVar6 + 0x48) = piVar3;
        if ((piVar4 != (int *)0x0) && (*piVar4 + 1 != 0)) {
          *piVar4 = *piVar4 + 1;
        }
        *(int **)(lVar6 + 0x58) = piVar4;
        if ((piVar1 != (int *)0x0) && (*piVar1 + 1 != 0)) {
          *piVar1 = *piVar1 + 1;
        }
        *(int **)(lVar6 + 0x60) = piVar1;
        *(undefined8 *)(lVar6 + 0x68) = 0;
        PyObject_GC_Track(lVar6);
        if (*(int *)pcVar5 < 0) {
          return lVar6;
        }
        *(longlong *)pcVar5 = *(longlong *)pcVar5 + -1;
        if (*(longlong *)pcVar5 != 0) {
          return lVar6;
        }
        _Py_Dealloc(pcVar5);
        return lVar6;
      }
      goto LAB_18000220f;
    }
  }
  pcVar5 = _Py_NoneStruct_exref;
  if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
    *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
  }
LAB_18000220f:
  FUN_18000d220("_security_crypto.encrypt_blob.genexpr",lVar7,0x23,
                PTR_s__security_crypto_py_180011d38);
  if ((-1 < *(int *)pcVar5) &&
     (*(longlong *)pcVar5 = *(longlong *)pcVar5 + -1, *(longlong *)pcVar5 == 0)) {
    _Py_Dealloc(pcVar5);
  }
  return 0;
}



// ==== FUN_180002260 @ 180002260 ====

undefined * FUN_180002260(longlong param_1,undefined *param_2,undefined *param_3)

{
  longlong lVar1;
  int iVar2;
  code *pcVar3;
  int *piVar4;
  undefined *puVar5;
  ulonglong uVar6;
  longlong *plVar7;
  code *pcVar8;
  code *pcVar9;
  char *pcVar10;
  longlong *plVar11;
  code *pcVar12;
  code *pcVar13;
  code *pcVar14;
  
  pcVar14 = (code *)0x0;
  lVar1 = *(longlong *)(param_1 + 0x18);
  pcVar10 = param_2;
  pcVar9 = pcVar14;
  if (*(int *)(param_1 + 0x70) == 0) {
    if ((code *)param_3 == _Py_NoneStruct_exref) {
      iVar2 = (int)*DAT_180016c20 + 1;
      if (iVar2 != 0) {
        *(int *)DAT_180016c20 = iVar2;
      }
      plVar11 = DAT_180016c20;
      pcVar3 = *(code **)(lVar1 + 0x18);
      if (pcVar3 == (code *)0x0) {
        pcVar10 = "local variable \'%s\' referenced before assignment";
        PyErr_Format(*(undefined8 *)PyExc_UnboundLocalError_exref,
                     "local variable \'%s\' referenced before assignment",&DAT_180010770);
        pcVar3 = pcVar14;
      }
      else {
        if ((*(code **)(pcVar3 + 8) == PyList_Type_exref) ||
           (*(code **)(pcVar3 + 8) == PyTuple_Type_exref)) {
          pcVar12 = pcVar14;
          pcVar13 = pcVar14;
          if (*(int *)pcVar3 + 1 != 0) {
            *(int *)pcVar3 = *(int *)pcVar3 + 1;
          }
          goto LAB_180002450;
        }
        pcVar13 = (code *)0xffffffffffffffff;
        pcVar3 = (code *)PyObject_GetIter();
        if (pcVar3 != (code *)0x0) {
          pcVar12 = *(code **)(*(longlong *)(pcVar3 + 8) + 0xe0);
          param_3 = pcVar12;
          goto joined_r0x000180002383;
        }
      }
      goto LAB_1800024e3;
    }
    puVar5 = PTR_s__security_crypto_py_180011d38;
    if (param_3 != (undefined *)0x0) {
      pcVar10 = "can\'t send non-None value to a just-started generator";
      PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref);
      puVar5 = PTR_s__security_crypto_py_180011d38;
    }
  }
  else {
    if (*(int *)(param_1 + 0x70) != 1) {
      return (undefined *)0x0;
    }
    plVar11 = *(longlong **)(lVar1 + 0x30);
    pcVar3 = *(code **)(lVar1 + 0x38);
    pcVar13 = *(code **)(lVar1 + 0x40);
    pcVar12 = *(code **)(lVar1 + 0x48);
    *(undefined8 *)(lVar1 + 0x30) = 0;
    *(undefined8 *)(lVar1 + 0x38) = 0;
joined_r0x000180002383:
    if ((code *)param_3 == (code *)0x0) {
LAB_1800024e3:
      plVar7 = plVar11;
      pcVar8 = (code *)0x0;
      puVar5 = PTR_s__security_crypto_py_180011d38;
      if (plVar7 != (longlong *)0x0) goto LAB_1800025c6;
    }
    else {
      if (pcVar12 == (code *)0x0) {
LAB_180002450:
        if (*(longlong *)(pcVar3 + 0x10) <= (longlong)pcVar13) goto LAB_1800023d2;
        if (*(code **)(pcVar3 + 8) == PyList_Type_exref) {
          piVar4 = *(int **)(*(longlong *)(pcVar3 + 0x18) + (longlong)pcVar13 * 8);
        }
        else {
          piVar4 = *(int **)(pcVar3 + (longlong)pcVar13 * 8 + 0x18);
        }
        if (*piVar4 + 1 != 0) {
          *piVar4 = *piVar4 + 1;
        }
        pcVar13 = pcVar13 + 1;
        if (piVar4 != (int *)0x0) goto LAB_180002487;
        goto LAB_1800024e3;
      }
      piVar4 = (int *)(*pcVar12)(pcVar3);
      if (piVar4 == (int *)0x0) {
        puVar5 = (undefined *)PyErr_Occurred();
        if (puVar5 != (undefined *)0x0) {
          pcVar10 = *(char **)PyExc_StopIteration_exref;
          uVar6 = FUN_18000d500(puVar5,pcVar10);
          if ((int)uVar6 == 0) goto LAB_1800024e3;
          PyErr_Clear();
        }
LAB_1800023d2:
        if ((-1 < *(int *)pcVar3) &&
           (*(longlong *)pcVar3 = *(longlong *)pcVar3 + -1, *(longlong *)pcVar3 == 0)) {
          _Py_Dealloc(pcVar3);
        }
        if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
          _Py_Dealloc(plVar11);
        }
        pcVar14 = _Py_NoneStruct_exref;
        if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
          *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
        }
        goto LAB_18000240c;
      }
LAB_180002487:
      plVar7 = *(longlong **)(lVar1 + 0x20);
      *(int **)(lVar1 + 0x20) = piVar4;
      if (((plVar7 != (longlong *)0x0) && (-1 < (int)*plVar7)) &&
         (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
        _Py_Dealloc();
      }
      iVar2 = (int)*plVar11 + 1;
      if (iVar2 != 0) {
        *(int *)plVar11 = iVar2;
      }
      plVar7 = *(longlong **)(lVar1 + 0x28);
      *(longlong **)(lVar1 + 0x28) = plVar11;
      if (((plVar7 != (longlong *)0x0) && (-1 < (int)*plVar7)) &&
         (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
        _Py_Dealloc();
      }
      pcVar10 = (char *)DAT_180016c28;
      plVar7 = (longlong *)FUN_18000ad30((longlong)plVar11,(int *)DAT_180016c28);
      if (plVar7 == (longlong *)0x0) goto LAB_1800024e3;
      if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
        _Py_Dealloc(plVar11);
      }
      if (*(longlong *)(*(longlong *)(lVar1 + 0x10) + 0x10) == 0) {
        pcVar10 = "free variable \'%s\' referenced before assignment in enclosing scope";
        PyErr_Format(*(undefined8 *)PyExc_NameError_exref,
                     "free variable \'%s\' referenced before assignment in enclosing scope",
                     &DAT_180010774);
        pcVar8 = pcVar14;
      }
      else {
        pcVar8 = (code *)PyLong_FromSsize_t(*(undefined8 *)(*(longlong *)(lVar1 + 0x10) + 0x18));
        pcVar9 = (code *)0x0;
        if ((pcVar8 != (code *)0x0) &&
           (pcVar10 = (char *)pcVar8,
           pcVar9 = (code *)PyNumber_Remainder(*(undefined8 *)(lVar1 + 0x28)), pcVar9 != (code *)0x0
           )) {
          if ((-1 < *(int *)pcVar8) &&
             (*(longlong *)pcVar8 = *(longlong *)pcVar8 + -1, *(longlong *)pcVar8 == 0)) {
            _Py_Dealloc(pcVar8);
          }
          pcVar10 = (char *)pcVar9;
          pcVar8 = (code *)FUN_18000af90(*(longlong *)(*(longlong *)(lVar1 + 0x10) + 0x10),
                                         (longlong)pcVar9);
          if (pcVar8 != (code *)0x0) {
            if ((-1 < *(int *)pcVar9) &&
               (*(longlong *)pcVar9 = *(longlong *)pcVar9 + -1, *(longlong *)pcVar9 == 0)) {
              _Py_Dealloc(pcVar9);
            }
            pcVar10 = (char *)pcVar8;
            puVar5 = (undefined *)PyNumber_Xor(*(undefined8 *)(lVar1 + 0x20));
            pcVar9 = (code *)0x0;
            if (puVar5 != (undefined *)0x0) {
              if ((-1 < *(int *)pcVar8) &&
                 (*(longlong *)pcVar8 = *(longlong *)pcVar8 + -1, *(longlong *)pcVar8 == 0)) {
                _Py_Dealloc(pcVar8);
              }
              *(longlong **)(lVar1 + 0x30) = plVar7;
              *(code **)(lVar1 + 0x38) = pcVar3;
              *(code **)(lVar1 + 0x40) = pcVar13;
              *(code **)(lVar1 + 0x48) = pcVar12;
              plVar11 = *(longlong **)(param_1 + 0x20);
              if (((plVar11 != (longlong *)0x0) &&
                  (*(undefined8 *)(param_1 + 0x20) = 0, -1 < (int)*plVar11)) &&
                 (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
                _Py_Dealloc();
              }
              *(undefined4 *)(param_1 + 0x70) = 1;
              return puVar5;
            }
          }
        }
      }
LAB_1800025c6:
      puVar5 = PTR_s__security_crypto_py_180011d38;
      if ((-1 < (int)*plVar7) && (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
        _Py_Dealloc(plVar7);
      }
    }
    if (((pcVar3 != (code *)0x0) && (-1 < *(int *)pcVar3)) &&
       (*(longlong *)pcVar3 = *(longlong *)pcVar3 + -1, *(longlong *)pcVar3 == 0)) {
      _Py_Dealloc(pcVar3);
    }
    if (((pcVar8 != (code *)0x0) && (-1 < *(int *)pcVar8)) &&
       (*(longlong *)pcVar8 = *(longlong *)pcVar8 + -1, *(longlong *)pcVar8 == 0)) {
      _Py_Dealloc(pcVar8);
    }
    if (((pcVar9 != (code *)0x0) && (-1 < *(int *)pcVar9)) &&
       (*(longlong *)pcVar9 = *(longlong *)pcVar9 + -1, *(longlong *)pcVar9 == 0)) {
      _Py_Dealloc(pcVar9);
    }
  }
  if (*(longlong *)(param_2 + 0x70) != 0) {
    FUN_18000b1c0();
    FUN_18000d220("genexpr",pcVar10,0x23,puVar5);
  }
LAB_18000240c:
  *(undefined4 *)(param_1 + 0x70) = 0xffffffff;
  FUN_18000e840(param_1);
  return pcVar14;
}



// ==== FUN_1800026b0 @ 1800026b0 ====

/* WARNING: Function: __security_check_cookie replaced with injection: security_check_cookie */

undefined * FUN_1800026b0(undefined8 param_1,undefined *param_2)

{
  undefined *puVar1;
  int *piVar2;
  int iVar3;
  int iVar4;
  code *pcVar5;
  ulonglong uVar6;
  longlong lVar7;
  longlong *plVar8;
  longlong *plVar9;
  longlong *plVar10;
  longlong *plVar11;
  longlong *plVar13;
  undefined8 *puVar14;
  undefined *puVar15;
  undefined *puVar16;
  longlong *plVar17;
  code *pcVar18;
  bool bVar19;
  undefined1 auStack_a8 [32];
  longlong *local_88;
  longlong local_80;
  int *local_78;
  code *local_70;
  longlong *local_68;
  longlong *local_60 [4];
  undefined *local_40;
  undefined8 local_38;
  ulonglong local_30;
  undefined8 uVar12;
  
  puVar15 = DAT_180016780;
  local_30 = DAT_180015000 ^ (ulonglong)auStack_a8;
  plVar10 = (longlong *)0x0;
  local_60[0] = (longlong *)0x0;
  local_88 = (longlong *)0x0;
  local_60[2] = (longlong *)0x0;
  local_78 = (int *)param_2;
  if (DAT_180016ca8 < 1 || *(longlong *)(DAT_180016780 + 0x20) != 0x20) {
    puVar15 = (undefined *)0x0;
    pcVar5 = (code *)(**(code **)(DAT_180016780 + 0x130))(DAT_180016780);
    local_70 = pcVar5;
    if (pcVar5 != (code *)0x0) goto LAB_180002785;
LAB_180002e72:
    pcVar5 = _Py_NoneStruct_exref;
    if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
      *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
    }
    iVar3 = 0x1c;
    puVar16 = PTR_s__security_crypto_py_180011d38;
LAB_180002e92:
    FUN_18000d220("_security_crypto.encrypt_blob",puVar15,iVar3,puVar16);
    param_2 = (undefined *)0x0;
LAB_180002ea6:
    if (plVar10 != (longlong *)0x0) goto LAB_180002eab;
  }
  else {
    DAT_180016ca8 = DAT_180016ca8 + -1;
    pcVar5 = *(code **)(&DAT_180016c68 + (longlong)DAT_180016ca8 * 8);
    *(longlong *)pcVar5 = 0;
    *(longlong *)(pcVar5 + 8) = 0;
    *(longlong *)(pcVar5 + 0x10) = 0;
    *(longlong *)(pcVar5 + 0x18) = 0;
    local_70 = pcVar5;
    PyObject_Init(pcVar5);
    PyObject_GC_Track(pcVar5);
LAB_180002785:
    if (pcVar5 == (code *)0x0) goto LAB_180002e72;
    puVar15 = (undefined *)(ulonglong)((code *)param_2 == _Py_TrueStruct_exref);
    if (((code *)param_2 != _Py_FalseStruct_exref && (code *)param_2 != _Py_NoneStruct_exref) &&
        (code *)param_2 != _Py_TrueStruct_exref) {
      uVar6 = PyObject_IsTrue(param_2);
      puVar15 = (undefined *)(uVar6 & 0xffffffff);
    }
    iVar3 = (int)puVar15;
    if (iVar3 < 0) {
      iVar3 = 0x1d;
      puVar16 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180002e92;
    }
    bVar19 = iVar3 == 0;
    if (iVar3 != 0) {
      lVar7 = PyObject_Size(param_2);
      if (lVar7 == -1) {
        iVar3 = 0x1d;
        puVar16 = PTR_s__security_crypto_py_180011d38;
        goto LAB_180002e92;
      }
      bVar19 = lVar7 < 10;
    }
    if (bVar19) {
      if (*(int *)param_2 + 1 != 0) {
        *(int *)param_2 = *(int *)param_2 + 1;
      }
      goto LAB_180002edd;
    }
    local_80 = PyThreadState_GetUnchecked();
    puVar14 = *(undefined8 **)(local_80 + 0x78);
    do {
      pcVar18 = (code *)*puVar14;
      if ((pcVar18 != (code *)0x0) && (pcVar18 != _Py_NoneStruct_exref)) break;
      puVar14 = (undefined8 *)puVar14[1];
    } while (puVar14 != (undefined8 *)0x0);
    if ((pcVar18 == (code *)0x0) || (pcVar18 == _Py_NoneStruct_exref)) {
      pcVar18 = (code *)0x0;
      plVar17 = (longlong *)0x0;
      plVar8 = (longlong *)0x0;
    }
    else {
      if (*(int *)pcVar18 + 1 != 0) {
        *(int *)pcVar18 = *(int *)pcVar18 + 1;
      }
      plVar17 = *(longlong **)(pcVar18 + 8);
      iVar3 = (int)*plVar17 + 1;
      if (iVar3 != 0) {
        *(int *)plVar17 = iVar3;
      }
      plVar8 = (longlong *)PyException_GetTraceback(pcVar18);
    }
    plVar13 = (longlong *)0x0;
    plVar9 = (longlong *)FUN_18000a140(DAT_180016b80);
    if (plVar9 == (longlong *)0x0) {
      iVar3 = 0x20;
      puVar16 = PTR_s__security_crypto_py_180011d38;
      pcVar5 = local_70;
LAB_1800029e0:
      lVar7 = local_80;
      puVar15 = *(undefined **)PyExc_Exception_exref;
      if (*(longlong *)(local_80 + 0x70) == 0) {
LAB_180002da0:
        plVar13 = (longlong *)**(undefined8 **)(lVar7 + 0x78);
        **(undefined8 **)(lVar7 + 0x78) = pcVar18;
        if (((plVar13 != (longlong *)0x0) && (-1 < (int)*plVar13)) &&
           (*plVar13 = *plVar13 + -1, *plVar13 == 0)) {
          _Py_Dealloc();
        }
        if (((plVar17 != (longlong *)0x0) && (-1 < (int)*plVar17)) &&
           (*plVar17 = *plVar17 + -1, *plVar17 == 0)) {
          _Py_Dealloc(plVar17);
        }
        if (((plVar8 != (longlong *)0x0) && (-1 < (int)*plVar8)) &&
           (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
          _Py_Dealloc(plVar8);
        }
        goto LAB_180002e92;
      }
      puVar1 = *(undefined **)(*(longlong *)(local_80 + 0x70) + 8);
      if (puVar1 != puVar15) {
        if ((*(uint *)(*(longlong *)(puVar15 + 8) + 0xa8) & 0x4000000) == 0) {
          uVar6 = FUN_18000d500(puVar1,puVar15);
          iVar4 = (int)uVar6;
        }
        else {
          uVar12 = FUN_180009f30(puVar1,(longlong)puVar15);
          iVar4 = (int)uVar12;
        }
        if (iVar4 == 0) goto LAB_180002da0;
      }
      plVar13 = *(longlong **)(lVar7 + 0x70);
      *(undefined8 *)(lVar7 + 0x70) = 0;
      if (((plVar13 != (longlong *)0x0) && (-1 < (int)*plVar13)) &&
         (*plVar13 = *plVar13 + -1, *plVar13 == 0)) {
        _Py_Dealloc();
      }
      param_2 = (undefined *)local_78;
      if (*local_78 + 1 != 0) {
        *local_78 = *local_78 + 1;
      }
      plVar13 = (longlong *)**(undefined8 **)(lVar7 + 0x78);
      **(undefined8 **)(lVar7 + 0x78) = pcVar18;
      if (((plVar13 != (longlong *)0x0) && (-1 < (int)*plVar13)) &&
         (*plVar13 = *plVar13 + -1, *plVar13 == 0)) {
        _Py_Dealloc();
      }
      if (((plVar17 != (longlong *)0x0) && (-1 < (int)*plVar17)) &&
         (*plVar17 = *plVar17 + -1, *plVar17 == 0)) {
        _Py_Dealloc(plVar17);
      }
      if (((plVar8 != (longlong *)0x0) && (-1 < (int)*plVar8)) &&
         (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
        _Py_Dealloc(plVar8);
      }
      goto LAB_180002ea6;
    }
    if (*(code **)(plVar9[1] + 0x90) == (code *)0x0) {
      plVar10 = (longlong *)PyObject_GetAttr(plVar9,DAT_180016968);
    }
    else {
      plVar10 = (longlong *)(**(code **)(plVar9[1] + 0x90))();
    }
    puVar16 = PTR_s__security_crypto_py_180011d38;
    if (plVar10 == (longlong *)0x0) {
      iVar3 = 0x20;
      pcVar5 = local_70;
      plVar10 = local_88;
      if (((int)local_88 <= (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
        _Py_Dealloc(plVar9);
        pcVar5 = local_70;
        plVar10 = local_88;
      }
      goto LAB_1800029e0;
    }
    if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
      _Py_Dealloc(plVar9);
    }
    lVar7 = 1;
    plVar9 = plVar10;
    if ((code *)plVar10[1] == PyMethod_Type_exref) {
      plVar13 = (longlong *)plVar10[3];
      plVar9 = (longlong *)plVar10[2];
      iVar3 = (int)*plVar13 + 1;
      if (iVar3 != 0) {
        *(int *)plVar13 = iVar3;
      }
      iVar3 = (int)*plVar9 + 1;
      if (iVar3 != 0) {
        *(int *)plVar9 = iVar3;
      }
      if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
        _Py_Dealloc(plVar10);
      }
      lVar7 = 0;
    }
    local_38 = 0;
    local_60[3] = plVar13;
    local_40 = param_2;
    plVar11 = (longlong *)PyTuple_New(1);
    uVar12 = DAT_180016c40;
    piVar2 = DAT_180016a58;
    puVar16 = PTR_s__security_crypto_py_180011d38;
    if (plVar11 == (longlong *)0x0) {
      if (((plVar9 != (longlong *)0x0) && (-1 < (int)*plVar9)) &&
         (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
        _Py_Dealloc(plVar9);
      }
      if (((plVar13 != (longlong *)0x0) && (-1 < (int)*plVar13)) &&
         (*plVar13 = *plVar13 + -1, *plVar13 == 0)) {
        _Py_Dealloc(plVar13);
      }
LAB_1800029d6:
      iVar3 = 0x20;
      pcVar5 = local_70;
      plVar10 = local_60[0];
      goto LAB_1800029e0;
    }
    plVar11[3] = (longlong)DAT_180016a58;
    iVar3 = *piVar2 + 1;
    if (iVar3 != 0) {
      *piVar2 = iVar3;
    }
    local_38 = uVar12;
    plVar10 = (longlong *)
              PyObject_Vectorcall(plVar9,local_60 + lVar7 + 3,2U - lVar7 | -lVar7 << 0x3f);
    if (((plVar13 != (longlong *)0x0) && (-1 < (int)*plVar13)) &&
       (*plVar13 = *plVar13 + -1, *plVar13 == 0)) {
      _Py_Dealloc(plVar13);
    }
    if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
      _Py_Dealloc(plVar11);
    }
    if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
      _Py_Dealloc(plVar9);
    }
    puVar16 = PTR_s__security_crypto_py_180011d38;
    if (plVar10 == (longlong *)0x0) goto LAB_1800029d6;
    plVar13 = (longlong *)0x0;
    plVar9 = (longlong *)FUN_18000a140(DAT_180016a80);
    if (plVar9 == (longlong *)0x0) {
      iVar3 = 0x21;
      puVar16 = PTR_s__security_crypto_py_180011d38;
      pcVar5 = local_70;
      goto LAB_1800029e0;
    }
    lVar7 = 1;
    plVar11 = plVar9;
    if ((code *)plVar9[1] == PyMethod_Type_exref) {
      plVar13 = (longlong *)plVar9[3];
      plVar11 = (longlong *)plVar9[2];
      iVar3 = (int)*plVar13 + 1;
      if (iVar3 != 0) {
        *(int *)plVar13 = iVar3;
      }
      iVar3 = (int)*plVar11 + 1;
      if (iVar3 != 0) {
        *(int *)plVar11 = iVar3;
      }
      if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
        _Py_Dealloc();
      }
      lVar7 = 0;
    }
    local_60[1] = (longlong *)0x0;
    local_60[0] = plVar13;
    plVar9 = (longlong *)
             FUN_18000a310((longlong)plVar11,local_60 + lVar7,1U - lVar7 | -lVar7 << 0x3f,0);
    if (((plVar13 != (longlong *)0x0) && (-1 < (int)*plVar13)) &&
       (*plVar13 = *plVar13 + -1, *plVar13 == 0)) {
      _Py_Dealloc(plVar13);
    }
    if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
      _Py_Dealloc(plVar11);
    }
    pcVar5 = local_70;
    if (plVar9 == (longlong *)0x0) {
      iVar3 = 0x21;
      puVar16 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800029e0;
    }
    *(longlong **)(local_70 + 0x10) = plVar9;
    iVar3 = (int)*plVar9 + 1;
    if (iVar3 != 0) {
      *(int *)plVar9 = iVar3;
    }
    lVar7 = PyObject_Size(plVar9);
    if (lVar7 == -1) {
      iVar3 = 0x22;
LAB_180002ccd:
      puVar16 = PTR_s__security_crypto_py_180011d38;
      if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
        _Py_Dealloc(plVar9);
      }
      goto LAB_1800029e0;
    }
    if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
      _Py_Dealloc(plVar9);
    }
    *(longlong *)(pcVar5 + 0x18) = lVar7;
    plVar13 = (longlong *)FUN_180002060((int *)pcVar5,(int *)plVar10);
    if (plVar13 == (longlong *)0x0) {
      iVar3 = 0x23;
      puVar16 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800029e0;
    }
    local_70 = (code *)0x0;
    local_68 = plVar13;
    plVar11 = (longlong *)FUN_18000a310((longlong)PyBytes_Type_exref,&local_68,0x8000000000000001,0)
    ;
    if ((-1 < (int)*plVar13) && (*plVar13 = *plVar13 + -1, *plVar13 == 0)) {
      _Py_Dealloc(plVar13);
    }
    if (plVar11 == (longlong *)0x0) {
      iVar3 = 0x23;
      puVar16 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800029e0;
    }
    local_60[2] = plVar11;
    plVar9 = (longlong *)FUN_18000a140(DAT_180016910);
    if (plVar9 == (longlong *)0x0) {
      iVar3 = 0x24;
      puVar16 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800029e0;
    }
    param_2 = (undefined *)PyNumber_Add(plVar9,plVar11);
    if ((int *)param_2 == (int *)0x0) {
      iVar3 = 0x24;
      goto LAB_180002ccd;
    }
    if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
      _Py_Dealloc(plVar9);
    }
    plVar13 = (longlong *)**(undefined8 **)(local_80 + 0x78);
    **(undefined8 **)(local_80 + 0x78) = pcVar18;
    if (((plVar13 != (longlong *)0x0) && (-1 < (int)*plVar13)) &&
       (*plVar13 = *plVar13 + -1, *plVar13 == 0)) {
      _Py_Dealloc();
    }
    if (((plVar17 != (longlong *)0x0) && (-1 < (int)*plVar17)) &&
       (*plVar17 = *plVar17 + -1, *plVar17 == 0)) {
      _Py_Dealloc(plVar17);
    }
    if (((plVar8 != (longlong *)0x0) && (-1 < (int)*plVar8)) &&
       (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
      _Py_Dealloc(plVar8);
    }
LAB_180002eab:
    if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
      _Py_Dealloc(plVar10);
    }
  }
  if (((local_60[2] != (longlong *)0x0) && (-1 < (int)*local_60[2])) &&
     (*local_60[2] = *local_60[2] + -1, *local_60[2] == 0)) {
    _Py_Dealloc();
  }
LAB_180002edd:
  if ((-1 < *(int *)pcVar5) &&
     (*(longlong *)pcVar5 = *(longlong *)pcVar5 + -1, *(longlong *)pcVar5 == 0)) {
    _Py_Dealloc(pcVar5);
  }
  return (undefined *)(int *)param_2;
}



// ==== FUN_180002f40 @ 180002f40 ====

undefined * FUN_180002f40(undefined8 param_1,char *param_2,longlong param_3,longlong param_4)

{
  int iVar1;
  longlong lVar2;
  undefined *puVar3;
  longlong *plVar4;
  longlong *local_res10;
  undefined *local_18;
  undefined8 local_10;
  
  local_res10 = (longlong *)0x0;
  local_18 = &DAT_180016978;
  local_10 = 0;
  if (param_4 == 0) {
LAB_180003051:
    if (param_3 == 1) {
      plVar4 = *(longlong **)param_2;
      iVar1 = (int)*plVar4 + 1;
      if (iVar1 != 0) {
        *(int *)plVar4 = iVar1;
      }
      goto LAB_1800030db;
    }
LAB_180003057:
    param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                 "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","decrypt_blob",
                 "exactly",1,&DAT_180010bad,param_3);
    plVar4 = (longlong *)0x0;
  }
  else {
    lVar2 = *(longlong *)(param_4 + 0x10);
    plVar4 = (longlong *)0x0;
    if (lVar2 < 0) goto LAB_180003096;
    if (lVar2 < 1) goto LAB_180003051;
    if (param_3 != 0) {
      if (param_3 != 1) goto LAB_180003057;
      local_res10 = *(longlong **)param_2;
      iVar1 = (int)*local_res10 + 1;
      if (iVar1 != 0) {
        *(int *)local_res10 = iVar1;
      }
    }
    param_2 = param_2 + param_3 * 8;
    lVar2 = FUN_18000ac00(param_4,(undefined8 *)param_2,(longlong *)&local_18,param_4,
                          (longlong)&local_res10,param_3,lVar2,"decrypt_blob");
    plVar4 = local_res10;
    if (-1 < (int)lVar2) {
      for (; param_3 < 1; param_3 = param_3 + 1) {
        if ((&local_res10)[param_3] == (longlong *)0x0) {
          param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
          PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                       "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","decrypt_blob",
                       "exactly",1,&DAT_180010bad,param_3);
          plVar4 = local_res10;
          goto LAB_180003096;
        }
      }
LAB_1800030db:
      puVar3 = FUN_180003770(param_1,(undefined *)plVar4);
      if (plVar4 == (longlong *)0x0) {
        return puVar3;
      }
      if ((int)*plVar4 < 0) {
        return puVar3;
      }
      *plVar4 = *plVar4 + -1;
      if (*plVar4 != 0) {
        return puVar3;
      }
      _Py_Dealloc(plVar4);
      return puVar3;
    }
  }
LAB_180003096:
  puVar3 = PTR_s__security_crypto_py_180011d38;
  if (((plVar4 != (longlong *)0x0) && (-1 < (int)*plVar4)) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)
     ) {
    _Py_Dealloc(plVar4);
  }
  FUN_18000d220("_security_crypto.decrypt_blob",param_2,0x29,puVar3);
  return (undefined *)0x0;
}



// ==== FUN_180003120 @ 180003120 ====

longlong FUN_180003120(int *param_1,int *param_2)

{
  int *piVar1;
  int *piVar2;
  int *piVar3;
  int *piVar4;
  code *pcVar5;
  longlong lVar6;
  longlong lVar7;
  
  lVar7 = DAT_180016798;
  if (DAT_180016d80 < 1 || *(longlong *)(DAT_180016798 + 0x20) != 0x50) {
    lVar7 = 0;
    pcVar5 = (code *)(**(code **)(DAT_180016798 + 0x130))();
    if (pcVar5 != (code *)0x0) goto LAB_1800031bf;
  }
  else {
    DAT_180016d80 = DAT_180016d80 + -1;
    pcVar5 = *(code **)(&DAT_180016d40 + (longlong)DAT_180016d80 * 8);
    *(longlong *)pcVar5 = 0;
    *(longlong *)(pcVar5 + 8) = 0;
    *(longlong *)(pcVar5 + 0x10) = 0;
    *(longlong *)(pcVar5 + 0x18) = 0;
    *(longlong *)(pcVar5 + 0x20) = 0;
    *(longlong *)(pcVar5 + 0x28) = 0;
    *(longlong *)(pcVar5 + 0x30) = 0;
    *(longlong *)(pcVar5 + 0x38) = 0;
    *(longlong *)(pcVar5 + 0x40) = 0;
    *(longlong *)(pcVar5 + 0x48) = 0;
    PyObject_Init(pcVar5);
    PyObject_GC_Track(pcVar5);
LAB_1800031bf:
    if (pcVar5 != (code *)0x0) {
      *(int **)(pcVar5 + 0x10) = param_1;
      if (*param_1 + 1 != 0) {
        *param_1 = *param_1 + 1;
      }
      *(int **)(pcVar5 + 0x18) = param_2;
      if (*param_2 + 1 != 0) {
        *param_2 = *param_2 + 1;
      }
      piVar4 = DAT_180016b00;
      piVar3 = DAT_1800169f0;
      piVar2 = DAT_180016990;
      piVar1 = DAT_180016860;
      lVar6 = _PyObject_GC_New(DAT_180016da8);
      if (lVar6 != 0) {
        *(code **)(lVar6 + 0x18) = pcVar5;
        *(code **)(lVar6 + 0x10) = FUN_180003320;
        if (*(int *)pcVar5 + 1 != 0) {
          *(int *)pcVar5 = *(int *)pcVar5 + 1;
        }
        *(undefined1 *)(lVar6 + 0x74) = 0;
        *(undefined4 *)(lVar6 + 0x70) = 0;
        *(undefined8 *)(lVar6 + 0x30) = 0;
        *(undefined8 *)(lVar6 + 0x38) = 0;
        *(undefined8 *)(lVar6 + 0x40) = 0;
        *(undefined8 *)(lVar6 + 0x20) = 0;
        *(undefined8 *)(lVar6 + 0x28) = 0;
        if ((piVar2 != (int *)0x0) && (*piVar2 + 1 != 0)) {
          *piVar2 = *piVar2 + 1;
        }
        *(int **)(lVar6 + 0x50) = piVar2;
        if ((piVar3 != (int *)0x0) && (*piVar3 + 1 != 0)) {
          *piVar3 = *piVar3 + 1;
        }
        *(int **)(lVar6 + 0x48) = piVar3;
        if ((piVar4 != (int *)0x0) && (*piVar4 + 1 != 0)) {
          *piVar4 = *piVar4 + 1;
        }
        *(int **)(lVar6 + 0x58) = piVar4;
        if ((piVar1 != (int *)0x0) && (*piVar1 + 1 != 0)) {
          *piVar1 = *piVar1 + 1;
        }
        *(int **)(lVar6 + 0x60) = piVar1;
        *(undefined8 *)(lVar6 + 0x68) = 0;
        PyObject_GC_Track(lVar6);
        if (*(int *)pcVar5 < 0) {
          return lVar6;
        }
        *(longlong *)pcVar5 = *(longlong *)pcVar5 + -1;
        if (*(longlong *)pcVar5 != 0) {
          return lVar6;
        }
        _Py_Dealloc(pcVar5);
        return lVar6;
      }
      goto LAB_1800032cf;
    }
  }
  pcVar5 = _Py_NoneStruct_exref;
  if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
    *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
  }
LAB_1800032cf:
  FUN_18000d220("_security_crypto.decrypt_blob.genexpr",lVar7,0x31,
                PTR_s__security_crypto_py_180011d38);
  if ((-1 < *(int *)pcVar5) &&
     (*(longlong *)pcVar5 = *(longlong *)pcVar5 + -1, *(longlong *)pcVar5 == 0)) {
    _Py_Dealloc(pcVar5);
  }
  return 0;
}



// ==== FUN_180003320 @ 180003320 ====

undefined * FUN_180003320(longlong param_1,undefined *param_2,undefined *param_3)

{
  longlong lVar1;
  int iVar2;
  code *pcVar3;
  int *piVar4;
  undefined *puVar5;
  ulonglong uVar6;
  longlong *plVar7;
  code *pcVar8;
  code *pcVar9;
  char *pcVar10;
  longlong *plVar11;
  code *pcVar12;
  code *pcVar13;
  code *pcVar14;
  
  pcVar14 = (code *)0x0;
  lVar1 = *(longlong *)(param_1 + 0x18);
  pcVar10 = param_2;
  pcVar9 = pcVar14;
  if (*(int *)(param_1 + 0x70) == 0) {
    if ((code *)param_3 == _Py_NoneStruct_exref) {
      iVar2 = (int)*DAT_180016c20 + 1;
      if (iVar2 != 0) {
        *(int *)DAT_180016c20 = iVar2;
      }
      plVar11 = DAT_180016c20;
      pcVar3 = *(code **)(lVar1 + 0x18);
      if (pcVar3 == (code *)0x0) {
        pcVar10 = "local variable \'%s\' referenced before assignment";
        PyErr_Format(*(undefined8 *)PyExc_UnboundLocalError_exref,
                     "local variable \'%s\' referenced before assignment",&DAT_180010770);
        pcVar3 = pcVar14;
      }
      else {
        if ((*(code **)(pcVar3 + 8) == PyList_Type_exref) ||
           (*(code **)(pcVar3 + 8) == PyTuple_Type_exref)) {
          pcVar12 = pcVar14;
          pcVar13 = pcVar14;
          if (*(int *)pcVar3 + 1 != 0) {
            *(int *)pcVar3 = *(int *)pcVar3 + 1;
          }
          goto LAB_180003510;
        }
        pcVar13 = (code *)0xffffffffffffffff;
        pcVar3 = (code *)PyObject_GetIter();
        if (pcVar3 != (code *)0x0) {
          pcVar12 = *(code **)(*(longlong *)(pcVar3 + 8) + 0xe0);
          param_3 = pcVar12;
          goto joined_r0x000180003443;
        }
      }
      goto LAB_1800035a3;
    }
    puVar5 = PTR_s__security_crypto_py_180011d38;
    if (param_3 != (undefined *)0x0) {
      pcVar10 = "can\'t send non-None value to a just-started generator";
      PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref);
      puVar5 = PTR_s__security_crypto_py_180011d38;
    }
  }
  else {
    if (*(int *)(param_1 + 0x70) != 1) {
      return (undefined *)0x0;
    }
    plVar11 = *(longlong **)(lVar1 + 0x30);
    pcVar3 = *(code **)(lVar1 + 0x38);
    pcVar13 = *(code **)(lVar1 + 0x40);
    pcVar12 = *(code **)(lVar1 + 0x48);
    *(undefined8 *)(lVar1 + 0x30) = 0;
    *(undefined8 *)(lVar1 + 0x38) = 0;
joined_r0x000180003443:
    if ((code *)param_3 == (code *)0x0) {
LAB_1800035a3:
      plVar7 = plVar11;
      pcVar8 = (code *)0x0;
      puVar5 = PTR_s__security_crypto_py_180011d38;
      if (plVar7 != (longlong *)0x0) goto LAB_180003686;
    }
    else {
      if (pcVar12 == (code *)0x0) {
LAB_180003510:
        if (*(longlong *)(pcVar3 + 0x10) <= (longlong)pcVar13) goto LAB_180003492;
        if (*(code **)(pcVar3 + 8) == PyList_Type_exref) {
          piVar4 = *(int **)(*(longlong *)(pcVar3 + 0x18) + (longlong)pcVar13 * 8);
        }
        else {
          piVar4 = *(int **)(pcVar3 + (longlong)pcVar13 * 8 + 0x18);
        }
        if (*piVar4 + 1 != 0) {
          *piVar4 = *piVar4 + 1;
        }
        pcVar13 = pcVar13 + 1;
        if (piVar4 != (int *)0x0) goto LAB_180003547;
        goto LAB_1800035a3;
      }
      piVar4 = (int *)(*pcVar12)(pcVar3);
      if (piVar4 == (int *)0x0) {
        puVar5 = (undefined *)PyErr_Occurred();
        if (puVar5 != (undefined *)0x0) {
          pcVar10 = *(char **)PyExc_StopIteration_exref;
          uVar6 = FUN_18000d500(puVar5,pcVar10);
          if ((int)uVar6 == 0) goto LAB_1800035a3;
          PyErr_Clear();
        }
LAB_180003492:
        if ((-1 < *(int *)pcVar3) &&
           (*(longlong *)pcVar3 = *(longlong *)pcVar3 + -1, *(longlong *)pcVar3 == 0)) {
          _Py_Dealloc(pcVar3);
        }
        if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
          _Py_Dealloc(plVar11);
        }
        pcVar14 = _Py_NoneStruct_exref;
        if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
          *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
        }
        goto LAB_1800034cc;
      }
LAB_180003547:
      plVar7 = *(longlong **)(lVar1 + 0x20);
      *(int **)(lVar1 + 0x20) = piVar4;
      if (((plVar7 != (longlong *)0x0) && (-1 < (int)*plVar7)) &&
         (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
        _Py_Dealloc();
      }
      iVar2 = (int)*plVar11 + 1;
      if (iVar2 != 0) {
        *(int *)plVar11 = iVar2;
      }
      plVar7 = *(longlong **)(lVar1 + 0x28);
      *(longlong **)(lVar1 + 0x28) = plVar11;
      if (((plVar7 != (longlong *)0x0) && (-1 < (int)*plVar7)) &&
         (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
        _Py_Dealloc();
      }
      pcVar10 = (char *)DAT_180016c28;
      plVar7 = (longlong *)FUN_18000ad30((longlong)plVar11,(int *)DAT_180016c28);
      if (plVar7 == (longlong *)0x0) goto LAB_1800035a3;
      if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
        _Py_Dealloc(plVar11);
      }
      if (*(longlong *)(*(longlong *)(lVar1 + 0x10) + 0x10) == 0) {
        pcVar10 = "free variable \'%s\' referenced before assignment in enclosing scope";
        PyErr_Format(*(undefined8 *)PyExc_NameError_exref,
                     "free variable \'%s\' referenced before assignment in enclosing scope",
                     &DAT_180010774);
        pcVar8 = pcVar14;
      }
      else {
        pcVar8 = (code *)PyLong_FromSsize_t(*(undefined8 *)(*(longlong *)(lVar1 + 0x10) + 0x18));
        pcVar9 = (code *)0x0;
        if ((pcVar8 != (code *)0x0) &&
           (pcVar10 = (char *)pcVar8,
           pcVar9 = (code *)PyNumber_Remainder(*(undefined8 *)(lVar1 + 0x28)), pcVar9 != (code *)0x0
           )) {
          if ((-1 < *(int *)pcVar8) &&
             (*(longlong *)pcVar8 = *(longlong *)pcVar8 + -1, *(longlong *)pcVar8 == 0)) {
            _Py_Dealloc(pcVar8);
          }
          pcVar10 = (char *)pcVar9;
          pcVar8 = (code *)FUN_18000af90(*(longlong *)(*(longlong *)(lVar1 + 0x10) + 0x10),
                                         (longlong)pcVar9);
          if (pcVar8 != (code *)0x0) {
            if ((-1 < *(int *)pcVar9) &&
               (*(longlong *)pcVar9 = *(longlong *)pcVar9 + -1, *(longlong *)pcVar9 == 0)) {
              _Py_Dealloc(pcVar9);
            }
            pcVar10 = (char *)pcVar8;
            puVar5 = (undefined *)PyNumber_Xor(*(undefined8 *)(lVar1 + 0x20));
            pcVar9 = (code *)0x0;
            if (puVar5 != (undefined *)0x0) {
              if ((-1 < *(int *)pcVar8) &&
                 (*(longlong *)pcVar8 = *(longlong *)pcVar8 + -1, *(longlong *)pcVar8 == 0)) {
                _Py_Dealloc(pcVar8);
              }
              *(longlong **)(lVar1 + 0x30) = plVar7;
              *(code **)(lVar1 + 0x38) = pcVar3;
              *(code **)(lVar1 + 0x40) = pcVar13;
              *(code **)(lVar1 + 0x48) = pcVar12;
              plVar11 = *(longlong **)(param_1 + 0x20);
              if (((plVar11 != (longlong *)0x0) &&
                  (*(undefined8 *)(param_1 + 0x20) = 0, -1 < (int)*plVar11)) &&
                 (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
                _Py_Dealloc();
              }
              *(undefined4 *)(param_1 + 0x70) = 1;
              return puVar5;
            }
          }
        }
      }
LAB_180003686:
      puVar5 = PTR_s__security_crypto_py_180011d38;
      if ((-1 < (int)*plVar7) && (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
        _Py_Dealloc(plVar7);
      }
    }
    if (((pcVar3 != (code *)0x0) && (-1 < *(int *)pcVar3)) &&
       (*(longlong *)pcVar3 = *(longlong *)pcVar3 + -1, *(longlong *)pcVar3 == 0)) {
      _Py_Dealloc(pcVar3);
    }
    if (((pcVar8 != (code *)0x0) && (-1 < *(int *)pcVar8)) &&
       (*(longlong *)pcVar8 = *(longlong *)pcVar8 + -1, *(longlong *)pcVar8 == 0)) {
      _Py_Dealloc(pcVar8);
    }
    if (((pcVar9 != (code *)0x0) && (-1 < *(int *)pcVar9)) &&
       (*(longlong *)pcVar9 = *(longlong *)pcVar9 + -1, *(longlong *)pcVar9 == 0)) {
      _Py_Dealloc(pcVar9);
    }
  }
  if (*(longlong *)(param_2 + 0x70) != 0) {
    FUN_18000b1c0();
    FUN_18000d220("genexpr",pcVar10,0x31,puVar5);
  }
LAB_1800034cc:
  *(undefined4 *)(param_1 + 0x70) = 0xffffffff;
  FUN_18000e840(param_1);
  return pcVar14;
}



// ==== FUN_180003770 @ 180003770 ====

/* WARNING: Removing unreachable block (ram,0x000180003c6d) */
/* WARNING: Removing unreachable block (ram,0x000180003c77) */
/* WARNING: Removing unreachable block (ram,0x000180003c81) */

undefined * FUN_180003770(undefined8 param_1,undefined *param_2)

{
  code *pcVar1;
  int iVar2;
  code *pcVar3;
  ulonglong uVar4;
  longlong lVar5;
  longlong *plVar6;
  longlong ****pppplVar7;
  longlong *plVar8;
  longlong ****pppplVar9;
  longlong *plVar10;
  char *pcVar11;
  longlong **pplVar12;
  longlong lVar13;
  undefined *puVar14;
  longlong *plVar15;
  bool bVar16;
  longlong ***local_res8;
  longlong **local_70;
  longlong **local_68 [4];
  longlong ***local_48;
  longlong *local_40;
  
  pcVar11 = (char *)DAT_180016790;
  plVar8 = (longlong *)0x0;
  plVar10 = (longlong *)0x0;
  plVar15 = (longlong *)0x0;
  local_res8 = (longlong ***)0x0;
  if (DAT_180016d38 < 1 || DAT_180016790[4] != (longlong ***)0x20) {
    pcVar11 = (char *)0x0;
    pcVar3 = (code *)(*(code *)DAT_180016790[0x26])(DAT_180016790);
    if (pcVar3 != (code *)0x0) goto LAB_180003823;
LAB_180003d9d:
    pcVar3 = _Py_NoneStruct_exref;
    if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
      *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
    }
    iVar2 = 0x29;
    puVar14 = PTR_s__security_crypto_py_180011d38;
    plVar10 = plVar15;
LAB_180003dbd:
    FUN_18000d220("_security_crypto.decrypt_blob",pcVar11,iVar2,puVar14);
    param_2 = (undefined *)0x0;
    pppplVar9 = (longlong ****)local_res8;
    if ((longlong ****)local_res8 != (longlong ****)0x0) goto LAB_180003dde;
  }
  else {
    DAT_180016d38 = DAT_180016d38 + -1;
    pcVar3 = *(code **)(&DAT_180016cf8 + (longlong)DAT_180016d38 * 8);
    *(longlong *)pcVar3 = 0;
    *(longlong *)(pcVar3 + 8) = 0;
    *(longlong *)(pcVar3 + 0x10) = 0;
    *(longlong *)(pcVar3 + 0x18) = 0;
    PyObject_Init(pcVar3);
    PyObject_GC_Track(pcVar3);
LAB_180003823:
    if (pcVar3 == (code *)0x0) goto LAB_180003d9d;
    pcVar11 = (char *)(ulonglong)((code *)param_2 == _Py_TrueStruct_exref);
    if (((code *)param_2 != _Py_FalseStruct_exref && (code *)param_2 != _Py_NoneStruct_exref) &&
        (code *)param_2 != _Py_TrueStruct_exref) {
      uVar4 = PyObject_IsTrue(param_2);
      pcVar11 = (char *)(uVar4 & 0xffffffff);
    }
    iVar2 = (int)pcVar11;
    if (iVar2 < 0) {
      iVar2 = 0x2a;
      puVar14 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180003dbd;
    }
    bVar16 = iVar2 == 0;
    if (iVar2 != 0) {
      lVar5 = PyObject_Size(param_2);
      if (lVar5 == -1) {
        iVar2 = 0x2a;
        puVar14 = PTR_s__security_crypto_py_180011d38;
        goto LAB_180003dbd;
      }
      bVar16 = lVar5 < 10;
    }
    if (bVar16) {
      if (*(int *)param_2 + 1 != 0) {
        *(int *)param_2 = *(int *)param_2 + 1;
      }
      goto LAB_180003e0f;
    }
    lVar5 = *(longlong *)(*(longlong *)(param_2 + 8) + 0x70);
    if ((lVar5 == 0) || (pcVar1 = *(code **)(lVar5 + 8), pcVar1 == (code *)0x0)) {
      pcVar11 = "\'%.200s\' object is unsliceable";
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"\'%.200s\' object is unsliceable",
                   *(undefined8 *)(*(longlong *)(param_2 + 8) + 0x18));
LAB_180003d96:
      iVar2 = 0x2c;
      puVar14 = PTR_s__security_crypto_py_180011d38;
      plVar10 = plVar15;
      goto LAB_180003dbd;
    }
    pcVar11 = (char *)DAT_180016818;
    plVar6 = (longlong *)(*pcVar1)(param_2);
    if (plVar6 == (longlong *)0x0) goto LAB_180003d96;
    pppplVar7 = (longlong ****)FUN_18000a140(DAT_180016910);
    if (pppplVar7 == (longlong ****)0x0) {
      iVar2 = 0x2c;
LAB_180003c16:
      puVar14 = PTR_s__security_crypto_py_180011d38;
      if ((-1 < (int)*plVar6) && (*plVar6 = *plVar6 + -1, *plVar6 == 0)) {
        _Py_Dealloc(plVar6);
      }
      if (((pppplVar7 != (longlong ****)0x0) && (-1 < *(int *)pppplVar7)) &&
         (*pppplVar7 = (longlong ***)((longlong)*pppplVar7 + -1), *pppplVar7 == (longlong ***)0x0))
      {
        _Py_Dealloc(pppplVar7);
      }
      if (plVar8 != (longlong *)0x0) {
LAB_180003c50:
        if ((-1 < (int)*plVar8) && (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
          _Py_Dealloc(plVar8);
        }
      }
      goto LAB_180003dbd;
    }
    pcVar11 = (char *)pppplVar7;
    plVar8 = (longlong *)PyObject_RichCompare(plVar6,pppplVar7,2);
    if (plVar8 == (longlong *)0x0) {
      iVar2 = 0x2c;
      goto LAB_180003c16;
    }
    if ((-1 < (int)*plVar6) && (*plVar6 = *plVar6 + -1, *plVar6 == 0)) {
      _Py_Dealloc(plVar6);
    }
    if ((-1 < *(int *)pppplVar7) &&
       (*pppplVar7 = (longlong ***)((longlong)*pppplVar7 + -1), *pppplVar7 == (longlong ***)0x0)) {
      _Py_Dealloc(pppplVar7);
    }
    iVar2 = FUN_18000ef60((undefined *)plVar8);
    if (iVar2 < 0) {
      iVar2 = 0x2c;
      puVar14 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180003c50;
    }
    if ((-1 < (int)*plVar8) && (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
      _Py_Dealloc(plVar8);
    }
    if (iVar2 == 0) {
      pcVar11 = (char *)&local_70;
      local_70 = (longlong **)DAT_1800168f0;
      plVar8 = (longlong *)
               FUN_18000a310(*(longlong *)PyExc_ValueError_exref,(undefined8 *)pcVar11,
                             0x8000000000000001,0);
      if (plVar8 == (longlong *)0x0) {
        iVar2 = 0x2d;
        puVar14 = PTR_s__security_crypto_py_180011d38;
      }
      else {
        pcVar11 = (char *)0x0;
        FUN_18000b360((undefined *)plVar8,(undefined *)0x0,(undefined *)0x0);
        if ((-1 < (int)*plVar8) && (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
          _Py_Dealloc(plVar8);
        }
        iVar2 = 0x2d;
        puVar14 = PTR_s__security_crypto_py_180011d38;
        plVar10 = plVar15;
      }
      goto LAB_180003dbd;
    }
    lVar5 = *(longlong *)(*(longlong *)(param_2 + 8) + 0x70);
    if ((lVar5 == 0) || (pcVar1 = *(code **)(lVar5 + 8), pcVar1 == (code *)0x0)) {
      pcVar11 = "\'%.200s\' object is unsliceable";
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"\'%.200s\' object is unsliceable",
                   *(undefined8 *)(*(longlong *)(param_2 + 8) + 0x18));
LAB_180003d74:
      iVar2 = 0x2e;
      puVar14 = PTR_s__security_crypto_py_180011d38;
      plVar10 = plVar15;
      goto LAB_180003dbd;
    }
    pcVar11 = (char *)DAT_180016820;
    pppplVar9 = (longlong ****)(*pcVar1)(param_2);
    if (pppplVar9 == (longlong ****)0x0) goto LAB_180003d74;
    pplVar12 = (longlong **)0x0;
    plVar8 = (longlong *)FUN_18000a140(DAT_180016a80);
    local_res8 = (longlong ***)pppplVar9;
    if (plVar8 == (longlong *)0x0) {
      iVar2 = 0x2f;
      puVar14 = PTR_s__security_crypto_py_180011d38;
      plVar10 = plVar15;
      goto LAB_180003dbd;
    }
    lVar13 = 1;
    lVar5 = 1;
    plVar6 = plVar8;
    if ((code *)plVar8[1] == PyMethod_Type_exref) {
      pplVar12 = (longlong **)plVar8[3];
      plVar6 = (longlong *)plVar8[2];
      if (*(int *)pplVar12 + 1 != 0) {
        *(int *)pplVar12 = *(int *)pplVar12 + 1;
      }
      iVar2 = (int)*plVar6 + 1;
      if (iVar2 != 0) {
        *(int *)plVar6 = iVar2;
      }
      if ((-1 < (int)*plVar8) && (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
        _Py_Dealloc();
      }
      lVar5 = 0;
    }
    local_68[1] = (longlong **)0x0;
    pcVar11 = (char *)(local_68 + lVar5);
    local_68[0] = pplVar12;
    plVar8 = (longlong *)
             FUN_18000a310((longlong)plVar6,(undefined8 *)pcVar11,1U - lVar5 | -lVar5 << 0x3f,0);
    if (((pplVar12 != (longlong **)0x0) && (-1 < *(int *)pplVar12)) &&
       (*pplVar12 = (longlong *)((longlong)*pplVar12 + -1), *pplVar12 == (longlong *)0x0)) {
      _Py_Dealloc(pplVar12);
    }
    if ((-1 < (int)*plVar6) && (*plVar6 = *plVar6 + -1, *plVar6 == 0)) {
      _Py_Dealloc(plVar6);
    }
    if (plVar8 == (longlong *)0x0) {
      iVar2 = 0x2f;
      puVar14 = PTR_s__security_crypto_py_180011d38;
      plVar10 = plVar15;
      goto LAB_180003dbd;
    }
    *(longlong **)(pcVar3 + 0x10) = plVar8;
    iVar2 = (int)*plVar8 + 1;
    if (iVar2 != 0) {
      *(int *)plVar8 = iVar2;
    }
    lVar5 = PyObject_Size(plVar8);
    if (lVar5 == -1) {
      iVar2 = 0x30;
      puVar14 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180003c50;
    }
    if ((-1 < (int)*plVar8) && (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
      _Py_Dealloc(plVar8);
    }
    *(longlong *)(pcVar3 + 0x18) = lVar5;
    pcVar11 = (char *)pppplVar9;
    plVar8 = (longlong *)FUN_180003120((int *)pcVar3,(int *)pppplVar9);
    if (plVar8 == (longlong *)0x0) {
      iVar2 = 0x31;
      puVar14 = PTR_s__security_crypto_py_180011d38;
      plVar10 = plVar15;
      goto LAB_180003dbd;
    }
    pcVar11 = (char *)(local_68 + 3);
    local_68[2] = (longlong **)0x0;
    local_68[3] = (longlong **)plVar8;
    plVar10 = (longlong *)
              FUN_18000a310((longlong)PyBytes_Type_exref,(undefined8 *)pcVar11,0x8000000000000001,0)
    ;
    if ((-1 < (int)*plVar8) && (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
      _Py_Dealloc(plVar8);
    }
    if (plVar10 == (longlong *)0x0) {
      iVar2 = 0x31;
      puVar14 = PTR_s__security_crypto_py_180011d38;
      plVar10 = plVar15;
      goto LAB_180003dbd;
    }
    pppplVar7 = (longlong ****)0x0;
    plVar8 = (longlong *)0x0;
    plVar6 = (longlong *)FUN_18000a140(DAT_180016b80);
    if (plVar6 == (longlong *)0x0) {
      iVar2 = 0x32;
      puVar14 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180003dbd;
    }
    pcVar11 = (char *)DAT_180016980;
    if (*(code **)(plVar6[1] + 0x90) == (code *)0x0) {
      plVar15 = (longlong *)PyObject_GetAttr(plVar6);
    }
    else {
      plVar15 = (longlong *)(**(code **)(plVar6[1] + 0x90))();
    }
    if (plVar15 == (longlong *)0x0) {
      iVar2 = 0x32;
      goto LAB_180003c16;
    }
    if ((-1 < (int)*plVar6) && (*plVar6 = *plVar6 + -1, *plVar6 == 0)) {
      _Py_Dealloc(plVar6);
    }
    plVar8 = plVar15;
    if ((code *)plVar15[1] == PyMethod_Type_exref) {
      pppplVar7 = (longlong ****)plVar15[3];
      plVar8 = (longlong *)plVar15[2];
      if (*(int *)pppplVar7 + 1 != 0) {
        *(int *)pppplVar7 = *(int *)pppplVar7 + 1;
      }
      iVar2 = (int)*plVar8 + 1;
      if (iVar2 != 0) {
        *(int *)plVar8 = iVar2;
      }
      if ((-1 < (int)*plVar15) && (*plVar15 = *plVar15 + -1, *plVar15 == 0)) {
        _Py_Dealloc(plVar15);
      }
      lVar13 = 0;
    }
    pcVar11 = (char *)(&local_48 + lVar13);
    local_48 = (longlong ***)pppplVar7;
    local_40 = plVar10;
    param_2 = (undefined *)
              FUN_18000a310((longlong)plVar8,(undefined8 *)pcVar11,2U - lVar13 | -lVar13 << 0x3f,0);
    if (((pppplVar7 != (longlong ****)0x0) && (-1 < *(int *)pppplVar7)) &&
       (*pppplVar7 = (longlong ***)((longlong)*pppplVar7 + -1), *pppplVar7 == (longlong ***)0x0)) {
      _Py_Dealloc(pppplVar7);
    }
    if ((-1 < (int)*plVar8) && (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
      _Py_Dealloc(plVar8);
    }
    if (param_2 == (undefined *)0x0) {
      iVar2 = 0x32;
      puVar14 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180003dbd;
    }
LAB_180003dde:
    if ((-1 < *(int *)pppplVar9) &&
       (*pppplVar9 = (longlong ***)((longlong)*pppplVar9 + -1), *pppplVar9 == (longlong ***)0x0)) {
      _Py_Dealloc(pppplVar9);
    }
  }
  if (((plVar10 != (longlong *)0x0) && (-1 < (int)*plVar10)) &&
     (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
    _Py_Dealloc(plVar10);
  }
LAB_180003e0f:
  if ((-1 < *(int *)pcVar3) &&
     (*(longlong *)pcVar3 = *(longlong *)pcVar3 + -1, *(longlong *)pcVar3 == 0)) {
    _Py_Dealloc(pcVar3);
  }
  return param_2;
}



// ==== FUN_180003e60 @ 180003e60 ====

undefined * FUN_180003e60(longlong param_1,char *param_2,longlong param_3,longlong param_4)

{
  int iVar1;
  longlong lVar2;
  undefined *puVar3;
  longlong *plVar4;
  longlong *local_res10;
  undefined *local_18;
  undefined8 local_10;
  
  local_res10 = (longlong *)0x0;
  local_18 = &DAT_180016978;
  local_10 = 0;
  if (param_4 == 0) {
LAB_180003f6c:
    if (param_3 == 1) {
      plVar4 = *(longlong **)param_2;
      iVar1 = (int)*plVar4 + 1;
      if (iVar1 != 0) {
        *(int *)plVar4 = iVar1;
      }
      goto LAB_18000400b;
    }
LAB_180003f76:
    param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                 "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","decrypt_blob_safe",
                 "exactly",1,&DAT_180010bad,param_3);
    plVar4 = (longlong *)0x0;
  }
  else {
    lVar2 = *(longlong *)(param_4 + 0x10);
    plVar4 = (longlong *)0x0;
    if (lVar2 < 0) goto LAB_180003fb5;
    if (lVar2 < 1) goto LAB_180003f6c;
    if (param_3 != 0) {
      if (param_3 != 1) goto LAB_180003f76;
      local_res10 = *(longlong **)param_2;
      iVar1 = (int)*local_res10 + 1;
      if (iVar1 != 0) {
        *(int *)local_res10 = iVar1;
      }
    }
    param_2 = param_2 + param_3 * 8;
    lVar2 = FUN_18000ac00(param_4,(undefined8 *)param_2,(longlong *)&local_18,param_4,
                          (longlong)&local_res10,param_3,lVar2,"decrypt_blob_safe");
    plVar4 = local_res10;
    if (-1 < (int)lVar2) {
      for (; param_1 = param_4, param_3 < 1; param_3 = param_3 + 1) {
        if ((&local_res10)[param_3] == (longlong *)0x0) {
          param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
          PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                       "%.200s() takes %.8s %zd positional argument%.1s (%zd given)",
                       "decrypt_blob_safe","exactly",1,&DAT_180010bad,param_3);
          plVar4 = local_res10;
          goto LAB_180003fb5;
        }
      }
LAB_18000400b:
      puVar3 = FUN_180004050(param_1,(undefined *)plVar4);
      if (((plVar4 != (longlong *)0x0) && (-1 < (int)*plVar4)) &&
         (*plVar4 = *plVar4 + -1, *plVar4 == 0)) {
        _Py_Dealloc(plVar4);
      }
      return puVar3;
    }
  }
LAB_180003fb5:
  puVar3 = PTR_s__security_crypto_py_180011d38;
  if (((plVar4 != (longlong *)0x0) && (-1 < (int)*plVar4)) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)
     ) {
    _Py_Dealloc(plVar4);
  }
  FUN_18000d220("_security_crypto.decrypt_blob_safe",param_2,0x35,puVar3);
  return (undefined *)0x0;
}



// ==== FUN_180004050 @ 180004050 ====

undefined * FUN_180004050(undefined8 param_1,undefined *param_2)

{
  code *pcVar1;
  undefined *puVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  longlong lVar6;
  longlong *plVar7;
  longlong *plVar8;
  longlong *plVar9;
  longlong *plVar10;
  undefined *puVar11;
  ulonglong uVar13;
  undefined8 *puVar14;
  longlong lVar15;
  longlong *plVar16;
  code *pcVar17;
  undefined *local_res8;
  longlong *local_48 [2];
  undefined8 uVar12;
  
  plVar10 = (longlong *)0x0;
  puVar11 = (undefined *)(ulonglong)((code *)param_2 == _Py_TrueStruct_exref);
  if (((code *)param_2 != _Py_NoneStruct_exref && (code *)param_2 != _Py_FalseStruct_exref) &&
      (code *)param_2 != _Py_TrueStruct_exref) {
    uVar3 = PyObject_IsTrue(param_2);
    puVar11 = (undefined *)(ulonglong)uVar3;
  }
  if ((int)puVar11 < 0) {
    iVar4 = 0x36;
    local_res8 = PTR_s__security_crypto_py_180011d38;
LAB_1800044de:
    FUN_18000d220("_security_crypto.decrypt_blob_safe",puVar11,iVar4,local_res8);
    param_2 = (undefined *)0x0;
  }
  else {
    if ((int)puVar11 == 0) {
      if (*(int *)param_2 + 1 == 0) {
        return param_2;
      }
      *(int *)param_2 = *(int *)param_2 + 1;
      return param_2;
    }
    lVar6 = PyThreadState_GetUnchecked();
    puVar14 = *(undefined8 **)(lVar6 + 0x78);
    do {
      pcVar17 = (code *)*puVar14;
      if ((pcVar17 != (code *)0x0) && (pcVar17 != _Py_NoneStruct_exref)) break;
      puVar14 = (undefined8 *)puVar14[1];
    } while (puVar14 != (undefined8 *)0x0);
    if ((pcVar17 == (code *)0x0) || (pcVar17 == _Py_NoneStruct_exref)) {
      pcVar17 = (code *)0x0;
      plVar16 = (longlong *)0x0;
      plVar7 = (longlong *)0x0;
    }
    else {
      if (*(int *)pcVar17 + 1 != 0) {
        *(int *)pcVar17 = *(int *)pcVar17 + 1;
      }
      plVar16 = *(longlong **)(pcVar17 + 8);
      iVar4 = (int)*plVar16 + 1;
      if (iVar4 != 0) {
        *(int *)plVar16 = iVar4;
      }
      plVar7 = (longlong *)PyException_GetTraceback(pcVar17);
    }
    lVar15 = *(longlong *)(*(longlong *)(param_2 + 8) + 0x70);
    if ((lVar15 == 0) || (pcVar1 = *(code **)(lVar15 + 8), pcVar1 == (code *)0x0)) {
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"\'%.200s\' object is unsliceable",
                   *(undefined8 *)(*(longlong *)(param_2 + 8) + 0x18));
LAB_1800043ac:
      iVar4 = 0x39;
      local_res8 = PTR_s__security_crypto_py_180011d38;
LAB_1800043bd:
      puVar11 = *(undefined **)PyExc_Exception_exref;
      if (*(longlong *)(lVar6 + 0x70) == 0) {
LAB_180004487:
        plVar10 = (longlong *)**(undefined8 **)(lVar6 + 0x78);
        **(undefined8 **)(lVar6 + 0x78) = pcVar17;
        if (((plVar10 != (longlong *)0x0) && (-1 < (int)*plVar10)) &&
           (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
          _Py_Dealloc();
        }
        if (((plVar16 != (longlong *)0x0) && (-1 < (int)*plVar16)) &&
           (*plVar16 = *plVar16 + -1, *plVar16 == 0)) {
          _Py_Dealloc(plVar16);
        }
        if (((plVar7 != (longlong *)0x0) && (-1 < (int)*plVar7)) &&
           (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
          _Py_Dealloc(plVar7);
        }
        goto LAB_1800044de;
      }
      puVar2 = *(undefined **)(*(longlong *)(lVar6 + 0x70) + 8);
      if (puVar2 != puVar11) {
        if ((*(uint *)(*(longlong *)(puVar11 + 8) + 0xa8) & 0x4000000) == 0) {
          uVar13 = FUN_18000d500(puVar2,puVar11);
          iVar5 = (int)uVar13;
        }
        else {
          uVar12 = FUN_180009f30(puVar2,(longlong)puVar11);
          iVar5 = (int)uVar12;
        }
        if (iVar5 == 0) goto LAB_180004487;
      }
      plVar10 = *(longlong **)(lVar6 + 0x70);
      *(undefined8 *)(lVar6 + 0x70) = 0;
      if (((plVar10 != (longlong *)0x0) && (-1 < (int)*plVar10)) &&
         (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
        _Py_Dealloc();
      }
      if (*(int *)param_2 + 1 != 0) {
        *(int *)param_2 = *(int *)param_2 + 1;
      }
      puVar14 = *(undefined8 **)(lVar6 + 0x78);
    }
    else {
      plVar8 = (longlong *)(*pcVar1)(param_2,DAT_180016818);
      if (plVar8 == (longlong *)0x0) goto LAB_1800043ac;
      plVar9 = (longlong *)FUN_18000a140(DAT_180016910);
      if ((plVar9 == (longlong *)0x0) ||
         (plVar10 = (longlong *)PyObject_RichCompare(plVar8,plVar9,2), plVar10 == (longlong *)0x0))
      {
        iVar4 = 0x39;
        local_res8 = PTR_s__security_crypto_py_180011d38;
        if ((-1 < (int)*plVar8) && (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
          _Py_Dealloc(plVar8);
        }
        if (((plVar9 != (longlong *)0x0) && (-1 < (int)*plVar9)) &&
           (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
          _Py_Dealloc(plVar9);
        }
        if (plVar10 != (longlong *)0x0) goto LAB_180004247;
        goto LAB_1800043bd;
      }
      if ((-1 < (int)*plVar8) && (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
        _Py_Dealloc(plVar8);
      }
      if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
        _Py_Dealloc(plVar9);
      }
      iVar4 = FUN_18000ef60((undefined *)plVar10);
      if (iVar4 < 0) {
        local_res8 = PTR_s__security_crypto_py_180011d38;
LAB_180004247:
        iVar4 = 0x39;
        if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
          _Py_Dealloc(plVar10);
        }
        goto LAB_1800043bd;
      }
      if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
        _Py_Dealloc(plVar10);
      }
      if (iVar4 != 0) {
        plVar10 = (longlong *)0x0;
        plVar8 = (longlong *)FUN_18000a140(DAT_180016988);
        if (plVar8 != (longlong *)0x0) {
          lVar15 = 1;
          plVar9 = plVar8;
          if ((code *)plVar8[1] == PyMethod_Type_exref) {
            plVar10 = (longlong *)plVar8[3];
            plVar9 = (longlong *)plVar8[2];
            iVar4 = (int)*plVar10 + 1;
            if (iVar4 != 0) {
              *(int *)plVar10 = iVar4;
            }
            iVar4 = (int)*plVar9 + 1;
            if (iVar4 != 0) {
              *(int *)plVar9 = iVar4;
            }
            if ((-1 < (int)*plVar8) && (*plVar8 = *plVar8 + -1, *plVar8 == 0)) {
              _Py_Dealloc();
            }
            lVar15 = 0;
          }
          local_48[0] = plVar10;
          local_48[1] = (longlong *)param_2;
          puVar11 = (undefined *)
                    FUN_18000a310((longlong)plVar9,local_48 + lVar15,2U - lVar15 | -lVar15 << 0x3f,0
                                 );
          if (((plVar10 != (longlong *)0x0) && (-1 < (int)*plVar10)) &&
             (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
            _Py_Dealloc(plVar10);
          }
          if ((-1 < (int)*plVar9) && (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
            _Py_Dealloc(plVar9);
          }
          if (puVar11 != (undefined *)0x0) {
            puVar14 = *(undefined8 **)(lVar6 + 0x78);
            param_2 = puVar11;
            goto LAB_180004437;
          }
        }
        iVar4 = 0x3a;
        local_res8 = PTR_s__security_crypto_py_180011d38;
        goto LAB_1800043bd;
      }
      if (*(int *)param_2 + 1 != 0) {
        *(int *)param_2 = *(int *)param_2 + 1;
      }
      puVar14 = *(undefined8 **)(lVar6 + 0x78);
    }
LAB_180004437:
    plVar10 = (longlong *)*puVar14;
    *puVar14 = pcVar17;
    if (((plVar10 != (longlong *)0x0) && (-1 < (int)*plVar10)) &&
       (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
      _Py_Dealloc();
    }
    if (((plVar16 != (longlong *)0x0) && (-1 < (int)*plVar16)) &&
       (*plVar16 = *plVar16 + -1, *plVar16 == 0)) {
      _Py_Dealloc(plVar16);
    }
    if (((plVar7 != (longlong *)0x0) && (-1 < (int)*plVar7)) &&
       (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
      _Py_Dealloc(plVar7);
    }
  }
  return param_2;
}



// ==== FUN_180004520 @ 180004520 ====

undefined * FUN_180004520(longlong param_1,char *param_2,longlong param_3,longlong param_4)

{
  int iVar1;
  longlong lVar2;
  undefined *puVar3;
  longlong *plVar4;
  longlong *local_res10;
  undefined *local_18;
  undefined8 local_10;
  
  local_res10 = (longlong *)0x0;
  local_18 = &DAT_180016978;
  local_10 = 0;
  if (param_4 == 0) {
LAB_18000462c:
    if (param_3 == 1) {
      plVar4 = *(longlong **)param_2;
      iVar1 = (int)*plVar4 + 1;
      if (iVar1 != 0) {
        *(int *)plVar4 = iVar1;
      }
      goto LAB_1800046cb;
    }
LAB_180004636:
    param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                 "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","is_encrypted",
                 "exactly",1,&DAT_180010bad,param_3);
    plVar4 = (longlong *)0x0;
  }
  else {
    lVar2 = *(longlong *)(param_4 + 0x10);
    plVar4 = (longlong *)0x0;
    if (lVar2 < 0) goto LAB_180004675;
    if (lVar2 < 1) goto LAB_18000462c;
    if (param_3 != 0) {
      if (param_3 != 1) goto LAB_180004636;
      local_res10 = *(longlong **)param_2;
      iVar1 = (int)*local_res10 + 1;
      if (iVar1 != 0) {
        *(int *)local_res10 = iVar1;
      }
    }
    param_2 = param_2 + param_3 * 8;
    lVar2 = FUN_18000ac00(param_4,(undefined8 *)param_2,(longlong *)&local_18,param_4,
                          (longlong)&local_res10,param_3,lVar2,"is_encrypted");
    plVar4 = local_res10;
    if (-1 < (int)lVar2) {
      for (; param_1 = param_4, param_3 < 1; param_3 = param_3 + 1) {
        if ((&local_res10)[param_3] == (longlong *)0x0) {
          param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
          PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                       "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","is_encrypted",
                       "exactly",1,&DAT_180010bad,param_3);
          plVar4 = local_res10;
          goto LAB_180004675;
        }
      }
LAB_1800046cb:
      puVar3 = FUN_180004710(param_1,(undefined *)plVar4);
      if (((plVar4 != (longlong *)0x0) && (-1 < (int)*plVar4)) &&
         (*plVar4 = *plVar4 + -1, *plVar4 == 0)) {
        _Py_Dealloc(plVar4);
      }
      return puVar3;
    }
  }
LAB_180004675:
  puVar3 = PTR_s__security_crypto_py_180011d38;
  if (((plVar4 != (longlong *)0x0) && (-1 < (int)*plVar4)) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)
     ) {
    _Py_Dealloc(plVar4);
  }
  FUN_18000d220("_security_crypto.is_encrypted",param_2,0x40,puVar3);
  return (undefined *)0x0;
}



// ==== FUN_180004710 @ 180004710 ====

undefined * FUN_180004710(undefined8 param_1,undefined *param_2)

{
  code *pcVar1;
  uint uVar2;
  longlong lVar3;
  longlong *plVar4;
  longlong *plVar5;
  undefined *puVar6;
  char *pcVar7;
  int iVar8;
  bool bVar9;
  
  uVar2 = (uint)((code *)param_2 == _Py_TrueStruct_exref);
  pcVar7 = param_2;
  if (((code *)param_2 != _Py_NoneStruct_exref && (code *)param_2 != _Py_FalseStruct_exref) &&
      (code *)param_2 != _Py_TrueStruct_exref) {
    uVar2 = PyObject_IsTrue(param_2);
  }
  if ((int)uVar2 < 0) {
LAB_180004770:
    iVar8 = 0x41;
    puVar6 = PTR_s__security_crypto_py_180011d38;
  }
  else {
    bVar9 = uVar2 == 0;
    if (uVar2 != 0) {
      lVar3 = PyObject_Size(param_2);
      if (lVar3 == -1) goto LAB_180004770;
      bVar9 = lVar3 < 3;
    }
    if (bVar9) {
      if (*(int *)_Py_FalseStruct_exref + 1 == 0) {
        return _Py_FalseStruct_exref;
      }
      *(int *)_Py_FalseStruct_exref = *(int *)_Py_FalseStruct_exref + 1;
      return _Py_FalseStruct_exref;
    }
    lVar3 = *(longlong *)(*(longlong *)(param_2 + 8) + 0x70);
    if ((lVar3 == 0) || (pcVar1 = *(code **)(lVar3 + 8), pcVar1 == (code *)0x0)) {
      pcVar7 = "\'%.200s\' object is unsliceable";
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"\'%.200s\' object is unsliceable",
                   *(undefined8 *)(*(longlong *)(param_2 + 8) + 0x18));
    }
    else {
      pcVar7 = (char *)DAT_180016818;
      plVar4 = (longlong *)(*pcVar1)(param_2);
      if (plVar4 != (longlong *)0x0) {
        plVar5 = (longlong *)FUN_18000a140(DAT_180016910);
        if ((plVar5 != (longlong *)0x0) &&
           (pcVar7 = (char *)plVar5, puVar6 = (undefined *)PyObject_RichCompare(plVar4,plVar5,2),
           puVar6 != (undefined *)0x0)) {
          if ((-1 < (int)*plVar4) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)) {
            _Py_Dealloc(plVar4);
          }
          if ((int)*plVar5 < 0) {
            return puVar6;
          }
          *plVar5 = *plVar5 + -1;
          if (*plVar5 != 0) {
            return puVar6;
          }
          _Py_Dealloc(plVar5);
          return puVar6;
        }
        puVar6 = PTR_s__security_crypto_py_180011d38;
        iVar8 = 0x43;
        if ((-1 < (int)*plVar4) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)) {
          _Py_Dealloc(plVar4);
        }
        if (((plVar5 != (longlong *)0x0) && (-1 < (int)*plVar5)) &&
           (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
          _Py_Dealloc(plVar5);
        }
        goto LAB_1800048bb;
      }
    }
    iVar8 = 0x43;
    puVar6 = PTR_s__security_crypto_py_180011d38;
  }
LAB_1800048bb:
  FUN_18000d220("_security_crypto.is_encrypted",pcVar7,iVar8,puVar6);
  return (undefined *)0x0;
}



// ==== FUN_1800048f0 @ 1800048f0 ====

undefined * FUN_1800048f0(void)

{
  int iVar1;
  code *pcVar2;
  undefined8 uVar3;
  
  uVar3 = DAT_180016908;
  iVar1 = PyDict_SetItem(DAT_180016730,DAT_180016908,DAT_180016b90);
  if (iVar1 < 0) {
    iVar1 = 0x49;
  }
  else {
    uVar3 = DAT_180016908;
    iVar1 = PyDict_SetItem(DAT_180016730,DAT_180016908,DAT_180016b98);
    if (-1 < iVar1) {
      pcVar2 = _Py_NoneStruct_exref;
      if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
        *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
      }
      return pcVar2;
    }
    iVar1 = 0x4a;
  }
  FUN_18000d220("_security_crypto._wipe_key",uVar3,iVar1,PTR_s__security_crypto_py_180011d38);
  return (undefined *)0x0;
}



// ==== FUN_180004980 @ 180004980 ====

/* WARNING: Removing unreachable block (ram,0x000180004a96) */
/* WARNING: Removing unreachable block (ram,0x000180004aa0) */
/* WARNING: Removing unreachable block (ram,0x000180004aaa) */

longlong FUN_180004980(undefined8 param_1,longlong **param_2)

{
  int iVar1;
  longlong *plVar2;
  longlong *plVar3;
  longlong **pplVar4;
  longlong *plVar5;
  longlong lVar6;
  longlong *plVar7;
  undefined *puVar8;
  longlong *local_38 [4];
  
  pplVar4 = (longlong **)0x0;
  plVar7 = (longlong *)0x0;
  plVar2 = (longlong *)FUN_18000a140(DAT_180016a08);
  puVar8 = PTR_s__security_crypto_py_180011d38;
  if (plVar2 == (longlong *)0x0) goto LAB_180004c0d;
  param_2 = DAT_180016b20;
  if (*(code **)(plVar2[1] + 0x90) == (code *)0x0) {
    plVar3 = (longlong *)PyObject_GetAttr(plVar2);
  }
  else {
    plVar3 = (longlong *)(**(code **)(plVar2[1] + 0x90))();
  }
  if (plVar3 == (longlong *)0x0) {
LAB_180004a3f:
    puVar8 = PTR_s__security_crypto_py_180011d38;
    if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
      _Py_Dealloc(plVar2);
    }
    if (plVar3 != (longlong *)0x0) goto LAB_180004a5f;
  }
  else {
    if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
      _Py_Dealloc(plVar2);
    }
    plVar2 = (longlong *)FUN_18000a140(DAT_180016920);
    puVar8 = PTR_s__security_crypto_py_180011d38;
    if (plVar2 != (longlong *)0x0) {
      pplVar4 = (longlong **)FUN_18000a140(DAT_180016918);
      if ((pplVar4 != (longlong **)0x0) &&
         (param_2 = pplVar4, plVar5 = (longlong *)PyNumber_Add(plVar2), plVar5 != (longlong *)0x0))
      {
        if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
          _Py_Dealloc(plVar2);
        }
        if ((-1 < *(int *)pplVar4) &&
           (*pplVar4 = (longlong *)((longlong)*pplVar4 + -1), *pplVar4 == (longlong *)0x0)) {
          _Py_Dealloc(pplVar4);
        }
        lVar6 = 1;
        plVar2 = plVar3;
        if ((code *)plVar3[1] == PyMethod_Type_exref) {
          plVar7 = (longlong *)plVar3[3];
          plVar2 = (longlong *)plVar3[2];
          iVar1 = (int)*plVar7 + 1;
          if (iVar1 != 0) {
            *(int *)plVar7 = iVar1;
          }
          iVar1 = (int)*plVar2 + 1;
          if (iVar1 != 0) {
            *(int *)plVar2 = iVar1;
          }
          if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
            _Py_Dealloc();
          }
          lVar6 = 0;
        }
        param_2 = local_38 + lVar6;
        local_38[0] = plVar7;
        local_38[1] = plVar5;
        plVar3 = (longlong *)FUN_18000a310((longlong)plVar2,param_2,2U - lVar6 | -lVar6 << 0x3f,0);
        if (((plVar7 != (longlong *)0x0) && (-1 < (int)*plVar7)) &&
           (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
          _Py_Dealloc(plVar7);
        }
        if ((-1 < (int)*plVar5) && (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
          _Py_Dealloc(plVar5);
        }
        if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
          _Py_Dealloc(plVar2);
        }
        puVar8 = PTR_s__security_crypto_py_180011d38;
        if (plVar3 != (longlong *)0x0) {
          iVar1 = (int)*plVar3 + 1;
          if (iVar1 != 0) {
            *(int *)plVar3 = iVar1;
          }
          param_2 = local_38 + 2;
          local_38[3] = (longlong *)0x0;
          local_38[2] = plVar3;
          lVar6 = PyObject_VectorcallMethod(DAT_1800169b0,param_2,0x8000000000000001,0);
          if (-1 < (int)*plVar3) {
            *plVar3 = *plVar3 + -1;
            if (*plVar3 == 0) {
              _Py_Dealloc(plVar3);
            }
            if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
              _Py_Dealloc(plVar3);
            }
          }
          puVar8 = PTR_s__security_crypto_py_180011d38;
          if (lVar6 != 0) {
            return lVar6;
          }
        }
        goto LAB_180004c0d;
      }
      goto LAB_180004a3f;
    }
LAB_180004a5f:
    if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
      _Py_Dealloc(plVar3);
    }
  }
  if (((pplVar4 != (longlong **)0x0) && (-1 < *(int *)pplVar4)) &&
     (*pplVar4 = (longlong *)((longlong)*pplVar4 + -1), *pplVar4 == (longlong *)0x0)) {
    _Py_Dealloc(pplVar4);
  }
LAB_180004c0d:
  FUN_18000d220("_security_crypto._pyc_derive_key",param_2,0x57,puVar8);
  return 0;
}



// ==== FUN_180004c50 @ 180004c50 ====

longlong FUN_180004c50(undefined8 param_1,char *param_2,longlong param_3,longlong param_4)

{
  undefined *puVar1;
  longlong lVar2;
  longlong ******pppppplVar3;
  longlong ******local_res10;
  undefined *local_18;
  undefined8 local_10;
  
  local_res10 = (longlong ******)0x0;
  local_18 = &DAT_180016af8;
  local_10 = 0;
  if (param_4 == 0) {
LAB_180004d61:
    if (param_3 == 1) {
      pppppplVar3 = *(longlong *******)param_2;
      if (*(int *)pppppplVar3 + 1 != 0) {
        *(int *)pppppplVar3 = *(int *)pppppplVar3 + 1;
      }
      goto LAB_180004deb;
    }
LAB_180004d67:
    param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                 "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","encrypt_pyc",
                 "exactly",1,&DAT_180010bad,param_3);
    pppppplVar3 = (longlong ******)0x0;
  }
  else {
    lVar2 = *(longlong *)(param_4 + 0x10);
    pppppplVar3 = (longlong ******)0x0;
    if (lVar2 < 0) goto LAB_180004da6;
    if (lVar2 < 1) goto LAB_180004d61;
    if (param_3 != 0) {
      if (param_3 != 1) goto LAB_180004d67;
      local_res10 = *(longlong *******)param_2;
      if (*(int *)local_res10 + 1 != 0) {
        *(int *)local_res10 = *(int *)local_res10 + 1;
      }
    }
    param_2 = param_2 + param_3 * 8;
    lVar2 = FUN_18000ac00(param_4,(undefined8 *)param_2,(longlong *)&local_18,param_4,
                          (longlong)&local_res10,param_3,lVar2,"encrypt_pyc");
    pppppplVar3 = local_res10;
    if (-1 < (int)lVar2) {
      for (; param_3 < 1; param_3 = param_3 + 1) {
        if ((&local_res10)[param_3] == (longlong ******)0x0) {
          param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
          PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                       "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","encrypt_pyc",
                       "exactly",1,&DAT_180010bad,param_3);
          pppppplVar3 = local_res10;
          goto LAB_180004da6;
        }
      }
LAB_180004deb:
      lVar2 = FUN_180004e30(param_1,pppppplVar3);
      if (pppppplVar3 == (longlong ******)0x0) {
        return lVar2;
      }
      if (*(int *)pppppplVar3 < 0) {
        return lVar2;
      }
      *pppppplVar3 = (longlong *****)((longlong)*pppppplVar3 + -1);
      if (*pppppplVar3 != (longlong *****)0x0) {
        return lVar2;
      }
      _Py_Dealloc(pppppplVar3);
      return lVar2;
    }
  }
LAB_180004da6:
  puVar1 = PTR_s__security_crypto_py_180011d38;
  if (((pppppplVar3 != (longlong ******)0x0) && (-1 < *(int *)pppppplVar3)) &&
     (*pppppplVar3 = (longlong *****)((longlong)*pppppplVar3 + -1),
     *pppppplVar3 == (longlong *****)0x0)) {
    _Py_Dealloc(pppppplVar3);
  }
  FUN_18000d220("_security_crypto.encrypt_pyc",param_2,0x5a,puVar1);
  return 0;
}



// ==== FUN_180004e30 @ 180004e30 ====

longlong FUN_180004e30(undefined8 param_1,longlong ******param_2)

{
  code *pcVar1;
  longlong ********pppppppplVar2;
  int iVar3;
  uint uVar4;
  longlong *******ppppppplVar5;
  longlong *plVar6;
  longlong ********pppppppplVar7;
  longlong lVar8;
  longlong *******ppppppplVar9;
  longlong *plVar10;
  longlong ********pppppppplVar11;
  longlong *******ppppppplVar12;
  longlong ********pppppppplVar13;
  code *pcVar14;
  longlong ********pppppppplVar15;
  longlong ********pppppppplVar16;
  longlong ********pppppppplVar17;
  longlong ********pppppppplVar18;
  undefined *puVar19;
  ulonglong uVar20;
  char *pcVar21;
  longlong ********pppppppplVar22;
  longlong *******local_res18;
  longlong *local_res20;
  longlong *******local_148;
  longlong *******local_140;
  longlong *local_138;
  longlong ******local_130;
  longlong *******local_128;
  longlong *******local_120;
  longlong *******local_118;
  longlong *local_110;
  longlong ******local_108;
  code *local_100;
  longlong ******local_f8;
  longlong *******local_f0 [2];
  longlong ******local_e0;
  undefined8 local_d8;
  undefined8 local_d0;
  longlong ******local_c8;
  longlong ******local_c0;
  longlong *local_b8;
  longlong ******local_b0;
  undefined8 local_a8;
  undefined8 local_a0;
  longlong ******local_98;
  longlong ******local_90;
  longlong *local_88;
  longlong ******local_80;
  undefined8 local_78;
  longlong ******local_70;
  undefined8 local_68;
  undefined8 local_60;
  longlong ******local_58 [3];
  
  pppppppplVar17 = (longlong ********)0x0;
  local_108 = (longlong ******)0x0;
  local_138 = (longlong *)0x0;
  local_128 = (longlong *******)0x0;
  local_130 = (longlong ******)0x0;
  local_140 = (longlong *******)0x0;
  local_res18 = (longlong *******)0x0;
  local_120 = (longlong *******)0x0;
  local_148 = (longlong *******)0x0;
  pcVar21 = (char *)param_2;
  ppppppplVar5 = (longlong *******)FUN_18000b560(DAT_180016ab8);
  if (ppppppplVar5 == (longlong *******)0x0) {
    iVar3 = 0x5c;
    local_res18 = (longlong *******)pppppppplVar17;
    puVar19 = PTR_s__security_crypto_py_180011d38;
LAB_180005f30:
    ppppppplVar5 = (longlong *******)local_108;
    FUN_18000d220("_security_crypto.encrypt_pyc",pcVar21,iVar3,puVar19);
    lVar8 = 0;
    pppppppplVar18 = (longlong ********)local_120;
    if (ppppppplVar5 == (longlong *******)0x0) goto LAB_180005fa5;
  }
  else {
    local_108 = (longlong ******)ppppppplVar5;
    plVar6 = (longlong *)FUN_18000a140(DAT_180016ae0);
    if (plVar6 == (longlong *)0x0) {
      iVar3 = 0x5d;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    lVar8 = 1;
    plVar10 = plVar6;
    pppppppplVar7 = pppppppplVar17;
    if ((code *)plVar6[1] == PyMethod_Type_exref) {
      pppppppplVar7 = (longlong ********)plVar6[3];
      plVar10 = (longlong *)plVar6[2];
      if (*(int *)pppppppplVar7 + 1 != 0) {
        *(int *)pppppppplVar7 = *(int *)pppppppplVar7 + 1;
      }
      iVar3 = (int)*plVar10 + 1;
      if (iVar3 != 0) {
        *(int *)plVar10 = iVar3;
      }
      if ((-1 < (int)*plVar6) && (*plVar6 = *plVar6 + -1, *plVar6 == 0)) {
        _Py_Dealloc();
      }
      lVar8 = 0;
    }
    local_f0[1] = (longlong *******)0x0;
    pcVar21 = (char *)(local_f0 + lVar8);
    local_f0[0] = (longlong *******)pppppppplVar7;
    plVar6 = (longlong *)
             FUN_18000a310((longlong)plVar10,(undefined8 *)pcVar21,1U - lVar8 | -lVar8 << 0x3f,0);
    if (((pppppppplVar7 != (longlong ********)0x0) && (-1 < *(int *)pppppppplVar7)) &&
       (*pppppppplVar7 = (longlong *******)((longlong)*pppppppplVar7 + -1),
       *pppppppplVar7 == (longlong *******)0x0)) {
      _Py_Dealloc(pppppppplVar7);
    }
    if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
      _Py_Dealloc(plVar10);
    }
    if (plVar6 == (longlong *)0x0) {
      iVar3 = 0x5d;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    if (*(int *)ppppppplVar5 + 1 != 0) {
      *(int *)ppppppplVar5 = *(int *)ppppppplVar5 + 1;
    }
    pcVar21 = (char *)&local_e0;
    local_d8 = DAT_180016c50;
    local_e0 = (longlong ******)ppppppplVar5;
    pppppppplVar7 =
         (longlong ********)PyObject_VectorcallMethod(DAT_180016b58,pcVar21,0x8000000000000002);
    if ((-1 < *(int *)ppppppplVar5) &&
       (*ppppppplVar5 = (longlong ******)((longlong)*ppppppplVar5 + -1),
       *ppppppplVar5 == (longlong ******)0x0)) {
      _Py_Dealloc(ppppppplVar5);
    }
    local_138 = plVar6;
    if (pppppppplVar7 == (longlong ********)0x0) {
      iVar3 = 0x5e;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    lVar8 = PyObject_Size(param_2);
    local_128 = (longlong *******)pppppppplVar7;
    if (lVar8 == -1) {
      iVar3 = 0x5f;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    ppppppplVar5 = (longlong *******)PyLong_FromSsize_t(lVar8);
    if (ppppppplVar5 == (longlong *******)0x0) {
      iVar3 = 0x5f;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    pcVar21 = (char *)&local_c8;
    local_d0 = 0;
    local_c8 = (longlong ******)ppppppplVar5;
    ppppppplVar9 = (longlong *******)
                   FUN_18000a310((longlong)PyByteArray_Type_exref,(undefined8 *)pcVar21,
                                 0x8000000000000001,0);
    if ((-1 < *(int *)ppppppplVar5) &&
       (*ppppppplVar5 = (longlong ******)((longlong)*ppppppplVar5 + -1),
       *ppppppplVar5 == (longlong ******)0x0)) {
      _Py_Dealloc(ppppppplVar5);
    }
    if (ppppppplVar9 == (longlong *******)0x0) {
      iVar3 = 0x5f;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    ppppppplVar5 = (longlong *******)0x0;
    plVar10 = (longlong *)FUN_18000a140(DAT_180016a08);
    local_130 = (longlong ******)ppppppplVar9;
    if (plVar10 == (longlong *)0x0) {
      iVar3 = 0x60;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    pcVar21 = (char *)DAT_180016b20;
    if (*(code **)(plVar10[1] + 0x90) == (code *)0x0) {
      pppppppplVar11 = (longlong ********)PyObject_GetAttr(plVar10);
    }
    else {
      pppppppplVar11 = (longlong ********)(**(code **)(plVar10[1] + 0x90))();
    }
    puVar19 = PTR_s__security_crypto_py_180011d38;
    if (pppppppplVar11 == (longlong ********)0x0) {
      local_res18 = (longlong *******)0x0;
      iVar3 = 0x60;
      local_140 = (longlong *******)0x0;
      if (-1 < (int)*plVar10) {
        *plVar10 = *plVar10 + -1;
        local_res18 = (longlong *******)0x0;
        local_140 = (longlong *******)0x0;
        if (*plVar10 == 0) {
          _Py_Dealloc(plVar10);
          local_res18 = (longlong *******)0x0;
          local_140 = (longlong *******)0x0;
        }
      }
      goto LAB_180005f30;
    }
    if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
      _Py_Dealloc(plVar10);
    }
    pcVar21 = (char *)pppppppplVar7;
    plVar10 = (longlong *)PyNumber_Add(plVar6);
    if (plVar10 == (longlong *)0x0) {
      iVar3 = 0x60;
      pppppppplVar18 = (longlong ********)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
LAB_180005ec2:
      if ((-1 < *(int *)pppppppplVar11) &&
         (*pppppppplVar11 = (longlong *******)((longlong)*pppppppplVar11 + -1),
         *pppppppplVar11 == (longlong *******)0x0)) {
        _Py_Dealloc(pppppppplVar11);
      }
LAB_180005ed6:
      pppppppplVar13 = pppppppplVar18;
      if ((longlong ********)local_148 != (longlong ********)0x0) {
LAB_180005ee0:
        pppppppplVar13 = pppppppplVar18;
        if ((-1 < *(int *)local_148) &&
           (*local_148 = (longlong ******)((longlong)*local_148 + -1),
           (longlong *******)*local_148 == (longlong *******)0x0)) {
          _Py_Dealloc(local_148);
        }
      }
      if (pppppppplVar17 != (longlong ********)0x0) {
LAB_180005ef9:
        if ((-1 < *(int *)pppppppplVar17) &&
           (*pppppppplVar17 = (longlong *******)((longlong)*pppppppplVar17 + -1),
           *pppppppplVar17 == (longlong *******)0x0)) {
          _Py_Dealloc(pppppppplVar17);
        }
      }
      if (((pppppppplVar13 != (longlong ********)0x0) && (-1 < *(int *)pppppppplVar13)) &&
         (*pppppppplVar13 = (longlong *******)((longlong)*pppppppplVar13 + -1),
         *pppppppplVar13 == (longlong *******)0x0)) {
        _Py_Dealloc(pppppppplVar13);
      }
      goto LAB_180005f30;
    }
    lVar8 = 1;
    pppppppplVar17 = pppppppplVar11;
    if (pppppppplVar11[1] == (longlong *******)PyMethod_Type_exref) {
      ppppppplVar5 = pppppppplVar11[3];
      pppppppplVar17 = (longlong ********)pppppppplVar11[2];
      if (*(int *)ppppppplVar5 + 1 != 0) {
        *(int *)ppppppplVar5 = *(int *)ppppppplVar5 + 1;
      }
      if (*(int *)pppppppplVar17 + 1 != 0) {
        *(int *)pppppppplVar17 = *(int *)pppppppplVar17 + 1;
      }
      if ((-1 < *(int *)pppppppplVar11) &&
         (*pppppppplVar11 = (longlong *******)((longlong)*pppppppplVar11 + -1),
         *pppppppplVar11 == (longlong *******)0x0)) {
        _Py_Dealloc();
      }
      lVar8 = 0;
    }
    pcVar21 = (char *)(&local_c0 + lVar8);
    local_c0 = (longlong ******)ppppppplVar5;
    local_b8 = plVar10;
    ppppppplVar12 =
         (longlong *******)
         FUN_18000a310((longlong)pppppppplVar17,(undefined8 *)pcVar21,2U - lVar8 | -lVar8 << 0x3f,0)
    ;
    if (((ppppppplVar5 != (longlong *******)0x0) && (-1 < *(int *)ppppppplVar5)) &&
       (*ppppppplVar5 = (longlong ******)((longlong)*ppppppplVar5 + -1),
       *ppppppplVar5 == (longlong ******)0x0)) {
      _Py_Dealloc(ppppppplVar5);
    }
    if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
      _Py_Dealloc(plVar10);
    }
    if ((-1 < *(int *)pppppppplVar17) &&
       (*pppppppplVar17 = (longlong *******)((longlong)*pppppppplVar17 + -1),
       *pppppppplVar17 == (longlong *******)0x0)) {
      _Py_Dealloc(pppppppplVar17);
    }
    pppppppplVar11 = (longlong ********)0x0;
    if (ppppppplVar12 == (longlong *******)0x0) {
      iVar3 = 0x60;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    if (*(int *)ppppppplVar12 + 1 != 0) {
      *(int *)ppppppplVar12 = *(int *)ppppppplVar12 + 1;
    }
    pcVar21 = (char *)&local_b0;
    local_a8 = 0;
    local_b0 = (longlong ******)ppppppplVar12;
    pppppppplVar13 =
         (longlong ********)PyObject_VectorcallMethod(DAT_1800169b0,pcVar21,0x8000000000000001);
    if (-1 < *(int *)ppppppplVar12) {
      *ppppppplVar12 = (longlong ******)((longlong)*ppppppplVar12 + -1);
      if (*ppppppplVar12 == (longlong ******)0x0) {
        _Py_Dealloc(ppppppplVar12);
      }
      if ((-1 < *(int *)ppppppplVar12) &&
         (*ppppppplVar12 = (longlong ******)((longlong)*ppppppplVar12 + -1),
         *ppppppplVar12 == (longlong ******)0x0)) {
        _Py_Dealloc(ppppppplVar12);
      }
    }
    if (pppppppplVar13 == (longlong ********)0x0) {
      iVar3 = 0x60;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    lVar8 = PyObject_Size(param_2);
    local_140 = (longlong *******)pppppppplVar13;
    if (lVar8 == -1) {
      iVar3 = 0x61;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    ppppppplVar5 = (longlong *******)PyLong_FromSsize_t(lVar8);
    if (ppppppplVar5 == (longlong *******)0x0) {
      iVar3 = 0x61;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    pcVar21 = (char *)&local_98;
    local_a0 = 0;
    local_98 = (longlong ******)ppppppplVar5;
    pcVar14 = (code *)FUN_18000a310((longlong)PyRange_Type_exref,(undefined8 *)pcVar21,
                                    0x8000000000000001,0);
    pppppppplVar22 = (longlong ********)0x0;
    if ((-1 < *(int *)ppppppplVar5) &&
       (*ppppppplVar5 = (longlong ******)((longlong)*ppppppplVar5 + -1),
       *ppppppplVar5 == (longlong ******)0x0)) {
      _Py_Dealloc(ppppppplVar5);
    }
    if (pcVar14 == (code *)0x0) {
      iVar3 = 0x61;
      local_res18 = (longlong *******)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    local_res20 = (longlong *)PyObject_GetIter(pcVar14);
    if (local_res20 == (longlong *)0x0) {
      iVar3 = 0x61;
LAB_1800058d9:
      puVar19 = PTR_s__security_crypto_py_180011d38;
      pppppppplVar16 = (longlong ********)0x0;
      pppppppplVar17 = (longlong ********)0x0;
      if ((-1 < *(int *)pcVar14) &&
         (*(longlong *)pcVar14 = *(longlong *)pcVar14 + -1, *(longlong *)pcVar14 == 0)) {
        _Py_Dealloc(pcVar14);
      }
      local_148 = (longlong *******)0x0;
      pppppppplVar18 = (longlong ********)0x0;
      pppppppplVar13 = pppppppplVar11;
      if (local_res20 != (longlong *)0x0) {
LAB_180005e76:
        pppppppplVar13 = pppppppplVar11;
        if ((-1 < (int)*local_res20) && (*local_res20 = *local_res20 + -1, *local_res20 == 0)) {
          _Py_Dealloc();
        }
      }
      pppppppplVar11 = pppppppplVar13;
      if (pppppppplVar22 != (longlong ********)0x0) {
LAB_180005e8c:
        pppppppplVar11 = pppppppplVar13;
        if ((-1 < *(int *)pppppppplVar22) &&
           (*pppppppplVar22 = (longlong *******)((longlong)*pppppppplVar22 + -1),
           *pppppppplVar22 == (longlong *******)0x0)) {
          _Py_Dealloc(pppppppplVar22);
        }
      }
      if (((pppppppplVar16 != (longlong ********)0x0) && (-1 < *(int *)pppppppplVar16)) &&
         (*pppppppplVar16 = (longlong *******)((longlong)*pppppppplVar16 + -1),
         *pppppppplVar16 == (longlong *******)0x0)) {
        _Py_Dealloc(pppppppplVar16);
      }
      if (pppppppplVar11 != (longlong ********)0x0) goto LAB_180005ec2;
      goto LAB_180005ed6;
    }
    pcVar1 = *(code **)(local_res20[1] + 0xe0);
    local_100 = pcVar1;
    if (pcVar1 == (code *)0x0) {
      iVar3 = 0x61;
      goto LAB_1800058d9;
    }
    if ((-1 < *(int *)pcVar14) &&
       (*(longlong *)pcVar14 = *(longlong *)pcVar14 + -1, *(longlong *)pcVar14 == 0)) {
      _Py_Dealloc(pcVar14);
    }
    pppppppplVar15 = (longlong ********)(*pcVar1)(local_res20);
    pppppppplVar2 = pppppppplVar13;
    local_res18 = (longlong *******)pppppppplVar11;
    while (local_140 = (longlong *******)pppppppplVar2, pppppppplVar15 != (longlong ********)0x0) {
      local_118 = (longlong *******)pppppppplVar13;
      if ((((longlong ********)local_res18 != (longlong ********)0x0) && (-1 < *(int *)local_res18))
         && (*local_res18 = (longlong ******)((longlong)*local_res18 + -1),
            (longlong *******)*local_res18 == (longlong *******)0x0)) {
        _Py_Dealloc(local_res18);
      }
      pcVar21 = (char *)DAT_180016c20;
      pcVar14 = (code *)PyObject_RichCompare(pppppppplVar15,DAT_180016c20,4);
      local_res18 = (longlong *******)pppppppplVar15;
      if (pcVar14 == (code *)0x0) {
LAB_1800059a0:
        iVar3 = 0x62;
LAB_1800059aa:
        pppppppplVar11 = (longlong ********)0x0;
        pppppppplVar22 = (longlong ********)0x0;
        pppppppplVar16 = (longlong ********)0x0;
        local_148 = (longlong *******)0x0;
        pppppppplVar17 = (longlong ********)0x0;
        pppppppplVar18 = (longlong ********)0x0;
        puVar19 = PTR_s__security_crypto_py_180011d38;
        goto LAB_180005e76;
      }
      uVar4 = (uint)(pcVar14 == _Py_TrueStruct_exref);
      if ((pcVar14 != _Py_NoneStruct_exref && pcVar14 != _Py_FalseStruct_exref) && uVar4 == 0) {
        uVar4 = PyObject_IsTrue(pcVar14);
      }
      if ((int)uVar4 < 0) {
LAB_1800059f7:
        pppppppplVar22 = (longlong ********)0x0;
        pppppppplVar11 = (longlong ********)0x0;
        iVar3 = 0x62;
        goto LAB_1800058d9;
      }
      if ((-1 < *(int *)pcVar14) &&
         (*(longlong *)pcVar14 = *(longlong *)pcVar14 + -1, *(longlong *)pcVar14 == 0)) {
        _Py_Dealloc(pcVar14);
      }
      if (uVar4 != 0) {
        pcVar21 = (char *)DAT_180016c60;
        pcVar14 = (code *)FUN_18000b6b0((int *)pppppppplVar15,DAT_180016c60);
        if (pcVar14 == (code *)0x0) goto LAB_1800059a0;
        pcVar21 = (char *)DAT_180016c20;
        uVar4 = FUN_18000b7a0((longlong)pcVar14,(longlong)DAT_180016c20);
        if ((int)uVar4 < 0) goto LAB_1800059f7;
        if ((-1 < *(int *)pcVar14) &&
           (*(longlong *)pcVar14 = *(longlong *)pcVar14 + -1, *(longlong *)pcVar14 == 0)) {
          _Py_Dealloc(pcVar14);
        }
        ppppppplVar5 = (longlong *******)0x0;
        pppppppplVar22 = (longlong ********)0x0;
        if (uVar4 != 0) {
          pppppppplVar16 = (longlong ********)FUN_18000a140(DAT_180016a08);
          if (pppppppplVar16 == (longlong ********)0x0) {
            pppppppplVar11 = (longlong ********)0x0;
            local_148 = (longlong *******)0x0;
            pppppppplVar17 = (longlong ********)0x0;
            iVar3 = 99;
            pppppppplVar18 = (longlong ********)0x0;
            puVar19 = PTR_s__security_crypto_py_180011d38;
          }
          else {
            pcVar21 = (char *)DAT_180016b20;
            if (pppppppplVar16[1][0x12] == (longlong ******)0x0) {
              local_148 = (longlong *******)PyObject_GetAttr(pppppppplVar16);
            }
            else {
              local_148 = (longlong *******)(*(code *)pppppppplVar16[1][0x12])();
            }
            if ((longlong ********)local_148 != (longlong ********)0x0) {
              if ((-1 < *(int *)pppppppplVar16) &&
                 (*pppppppplVar16 = (longlong *******)((longlong)*pppppppplVar16 + -1),
                 *pppppppplVar16 == (longlong *******)0x0)) {
                _Py_Dealloc(pppppppplVar16);
              }
              pcVar21 = (char *)pppppppplVar7;
              pppppppplVar16 = (longlong ********)PyNumber_Add(plVar6);
              if (pppppppplVar16 != (longlong ********)0x0) {
                pcVar21 = (char *)DAT_180016b50;
                if (pppppppplVar15[1][0x12] == (longlong ******)0x0) {
                  pppppppplVar17 = (longlong ********)PyObject_GetAttr(pppppppplVar15);
                }
                else {
                  pppppppplVar17 = (longlong ********)(*(code *)pppppppplVar15[1][0x12])();
                }
                if (pppppppplVar17 == (longlong ********)0x0) {
                  pppppppplVar11 = (longlong ********)0x0;
                  pppppppplVar18 = (longlong ********)0x0;
                  iVar3 = 99;
                  puVar19 = PTR_s__security_crypto_py_180011d38;
                }
                else {
                  pcVar21 = (char *)DAT_180016850;
                  pppppppplVar18 =
                       (longlong ********)FUN_18000a1d0((longlong)pppppppplVar17,DAT_180016850,0);
                  if (pppppppplVar18 != (longlong ********)0x0) {
                    if ((-1 < *(int *)pppppppplVar17) &&
                       (*pppppppplVar17 = (longlong *******)((longlong)*pppppppplVar17 + -1),
                       *pppppppplVar17 == (longlong *******)0x0)) {
                      _Py_Dealloc(pppppppplVar17);
                    }
                    pcVar21 = (char *)pppppppplVar18;
                    plVar10 = (longlong *)PyNumber_Add(pppppppplVar16);
                    pppppppplVar17 = (longlong ********)0x0;
                    if (plVar10 != (longlong *)0x0) {
                      if ((-1 < *(int *)pppppppplVar16) &&
                         (*pppppppplVar16 = (longlong *******)((longlong)*pppppppplVar16 + -1),
                         *pppppppplVar16 == (longlong *******)0x0)) {
                        _Py_Dealloc(pppppppplVar16);
                      }
                      pppppppplVar16 = (longlong ********)0x0;
                      if ((-1 < *(int *)pppppppplVar18) &&
                         (*pppppppplVar18 = (longlong *******)((longlong)*pppppppplVar18 + -1),
                         *pppppppplVar18 == (longlong *******)0x0)) {
                        _Py_Dealloc(pppppppplVar18);
                      }
                      pppppppplVar18 = (longlong ********)0x0;
                      lVar8 = 1;
                      pppppppplVar11 = (longlong ********)local_148;
                      if (local_148[1] == (longlong ******)PyMethod_Type_exref) {
                        ppppppplVar5 = (longlong *******)local_148[3];
                        pppppppplVar11 = (longlong ********)local_148[2];
                        if (*(int *)ppppppplVar5 + 1 != 0) {
                          *(int *)ppppppplVar5 = *(int *)ppppppplVar5 + 1;
                        }
                        if (*(int *)pppppppplVar11 + 1 != 0) {
                          *(int *)pppppppplVar11 = *(int *)pppppppplVar11 + 1;
                        }
                        if ((-1 < *(int *)local_148) &&
                           (*local_148 = (longlong ******)((longlong)*local_148 + -1),
                           (longlong *******)*local_148 == (longlong *******)0x0)) {
                          _Py_Dealloc();
                        }
                        lVar8 = 0;
                      }
                      pcVar21 = (char *)(&local_90 + lVar8);
                      local_90 = (longlong ******)ppppppplVar5;
                      local_88 = plVar10;
                      ppppppplVar12 =
                           (longlong *******)
                           FUN_18000a310((longlong)pppppppplVar11,(undefined8 *)pcVar21,
                                         2U - lVar8 | -lVar8 << 0x3f,0);
                      if (((ppppppplVar5 != (longlong *******)0x0) && (-1 < *(int *)ppppppplVar5))
                         && (*ppppppplVar5 = (longlong ******)((longlong)*ppppppplVar5 + -1),
                            *ppppppplVar5 == (longlong ******)0x0)) {
                        _Py_Dealloc(ppppppplVar5);
                      }
                      if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
                        _Py_Dealloc(plVar10);
                      }
                      pppppppplVar17 = (longlong ********)0x0;
                      if ((-1 < *(int *)pppppppplVar11) &&
                         (*pppppppplVar11 = (longlong *******)((longlong)*pppppppplVar11 + -1),
                         *pppppppplVar11 == (longlong *******)0x0)) {
                        _Py_Dealloc(pppppppplVar11);
                      }
                      local_148 = (longlong *******)0x0;
                      if (ppppppplVar12 == (longlong *******)0x0) {
                        iVar3 = 99;
                        pppppppplVar22 = (longlong ********)0x0;
                        pppppppplVar11 = (longlong ********)0x0;
                        puVar19 = PTR_s__security_crypto_py_180011d38;
                      }
                      else {
                        if (*(int *)ppppppplVar12 + 1 != 0) {
                          *(int *)ppppppplVar12 = *(int *)ppppppplVar12 + 1;
                        }
                        pcVar21 = (char *)&local_80;
                        local_78 = 0;
                        local_80 = (longlong ******)ppppppplVar12;
                        pppppppplVar13 =
                             (longlong ********)
                             PyObject_VectorcallMethod(DAT_1800169b0,pcVar21,0x8000000000000001);
                        if ((-1 < *(int *)ppppppplVar12) &&
                           (*ppppppplVar12 = (longlong ******)((longlong)*ppppppplVar12 + -1),
                           *ppppppplVar12 == (longlong ******)0x0)) {
                          _Py_Dealloc(ppppppplVar12);
                        }
                        pppppppplVar22 = (longlong ********)0x0;
                        if ((-1 < *(int *)ppppppplVar12) &&
                           (*ppppppplVar12 = (longlong ******)((longlong)*ppppppplVar12 + -1),
                           *ppppppplVar12 == (longlong ******)0x0)) {
                          _Py_Dealloc(ppppppplVar12);
                        }
                        pppppppplVar11 = (longlong ********)0x0;
                        if (pppppppplVar13 != (longlong ********)0x0) {
                          local_140 = (longlong *******)pppppppplVar13;
                          if ((-1 < *(int *)local_118) &&
                             (*local_118 = (longlong ******)((longlong)*local_118 + -1),
                             (longlong *******)*local_118 == (longlong *******)0x0)) {
                            _Py_Dealloc(pppppppplVar2);
                          }
                          goto LAB_180005776;
                        }
                        iVar3 = 99;
                        puVar19 = PTR_s__security_crypto_py_180011d38;
                      }
                      goto LAB_180005e76;
                    }
                  }
                  iVar3 = 99;
                  pppppppplVar11 = (longlong ********)0x0;
                  puVar19 = PTR_s__security_crypto_py_180011d38;
                }
                goto LAB_180005e76;
              }
            }
            pppppppplVar11 = (longlong ********)0x0;
            pppppppplVar17 = (longlong ********)0x0;
            iVar3 = 99;
            pppppppplVar18 = (longlong ********)0x0;
            puVar19 = PTR_s__security_crypto_py_180011d38;
          }
          goto LAB_180005e76;
        }
      }
LAB_180005776:
      pppppppplVar17 = (longlong ********)0x0;
      local_148 = (longlong *******)0x0;
      pcVar21 = (char *)pppppppplVar15;
      pcVar14 = (code *)FUN_18000af90((longlong)param_2,(longlong)pppppppplVar15);
      if (pcVar14 == (code *)0x0) {
        iVar3 = 100;
        goto LAB_1800059aa;
      }
      pcVar21 = (char *)DAT_180016c60;
      pppppppplVar11 = (longlong ********)FUN_18000b6b0((int *)pppppppplVar15,DAT_180016c60);
      pppppppplVar22 = pppppppplVar17;
      if ((pppppppplVar11 == (longlong ********)0x0) ||
         (pcVar21 = (char *)pppppppplVar11,
         pppppppplVar22 =
              (longlong ********)FUN_18000af90((longlong)pppppppplVar13,(longlong)pppppppplVar11),
         pppppppplVar22 == (longlong ********)0x0)) {
LAB_1800059dc:
        iVar3 = 100;
        goto LAB_1800058d9;
      }
      if ((-1 < *(int *)pppppppplVar11) &&
         (*pppppppplVar11 = (longlong *******)((longlong)*pppppppplVar11 + -1),
         *pppppppplVar11 == (longlong *******)0x0)) {
        _Py_Dealloc(pppppppplVar11);
      }
      pcVar21 = (char *)pppppppplVar22;
      pppppppplVar11 = (longlong ********)PyNumber_Xor(pcVar14);
      if (pppppppplVar11 == (longlong ********)0x0) goto LAB_1800059dc;
      if ((-1 < *(int *)pcVar14) &&
         (*(longlong *)pcVar14 = *(longlong *)pcVar14 + -1, *(longlong *)pcVar14 == 0)) {
        _Py_Dealloc(pcVar14);
      }
      if ((-1 < *(int *)pppppppplVar22) &&
         (*pppppppplVar22 = (longlong *******)((longlong)*pppppppplVar22 + -1),
         *pppppppplVar22 == (longlong *******)0x0)) {
        _Py_Dealloc(pppppppplVar22);
      }
      pppppppplVar22 = (longlong ********)0x0;
      pcVar21 = (char *)pppppppplVar15;
      iVar3 = PyObject_SetItem(ppppppplVar9,pppppppplVar15,pppppppplVar11);
      if (iVar3 < 0) {
        iVar3 = 100;
        pppppppplVar16 = (longlong ********)0x0;
        pppppppplVar18 = (longlong ********)0x0;
        puVar19 = PTR_s__security_crypto_py_180011d38;
        goto LAB_180005e76;
      }
      if ((-1 < *(int *)pppppppplVar11) &&
         (*pppppppplVar11 = (longlong *******)((longlong)*pppppppplVar11 + -1),
         *pppppppplVar11 == (longlong *******)0x0)) {
        _Py_Dealloc(pppppppplVar11);
      }
      pppppppplVar15 = (longlong ********)(*local_100)(local_res20);
      pppppppplVar2 = (longlong ********)local_140;
    }
    puVar19 = (undefined *)PyErr_Occurred();
    if (puVar19 != (undefined *)0x0) {
      pcVar21 = *(char **)PyExc_StopIteration_exref;
      uVar20 = FUN_18000d500(puVar19,pcVar21);
      if ((int)uVar20 != 0) {
        PyErr_Clear();
        goto LAB_180005a30;
      }
      local_148 = (longlong *******)0x0;
      pppppppplVar22 = (longlong ********)0x0;
      pppppppplVar18 = (longlong ********)0x0;
      iVar3 = 0x61;
      pppppppplVar11 = pppppppplVar18;
      pppppppplVar16 = (longlong ********)0x0;
      pppppppplVar17 = (longlong ********)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005e76;
    }
LAB_180005a30:
    if ((-1 < (int)*local_res20) && (*local_res20 = *local_res20 + -1, *local_res20 == 0)) {
      _Py_Dealloc(local_res20);
    }
    pppppppplVar13 = (longlong ********)0x0;
    pppppppplVar16 = (longlong ********)0x0;
    pppppppplVar18 = (longlong ********)0x0;
    local_148 = (longlong *******)FUN_18000a140(DAT_180016a08);
    if ((longlong ********)local_148 == (longlong ********)0x0) {
      iVar3 = 0x65;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    pcVar21 = (char *)DAT_180016b20;
    if ((longlong ******)local_148[1][0x12] == (longlong ******)0x0) {
      pppppppplVar17 = (longlong ********)PyObject_GetAttr(local_148);
    }
    else {
      pppppppplVar17 = (longlong ********)(*(code *)local_148[1][0x12])();
    }
    if (pppppppplVar17 == (longlong ********)0x0) {
      iVar3 = 0x65;
      pppppppplVar18 = pppppppplVar13;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005ee0;
    }
    if ((-1 < *(int *)local_148) &&
       (*local_148 = (longlong ******)((longlong)*local_148 + -1),
       (longlong *******)*local_148 == (longlong *******)0x0)) {
      _Py_Dealloc(local_148);
    }
    pcVar21 = (char *)&local_f8;
    local_100 = (code *)0x0;
    local_f8 = (longlong ******)ppppppplVar9;
    local_148 = (longlong *******)
                FUN_18000a310((longlong)PyBytes_Type_exref,(undefined8 *)pcVar21,0x8000000000000001,
                              0);
    if ((longlong ********)local_148 == (longlong ********)0x0) {
      iVar3 = 0x65;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005ef9;
    }
    pcVar21 = (char *)local_148;
    plVar6 = (longlong *)PyNumber_Add(plVar6);
    if (plVar6 == (longlong *)0x0) {
      iVar3 = 0x65;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005ee0;
    }
    if ((-1 < *(int *)local_148) &&
       (*local_148 = (longlong ******)((longlong)*local_148 + -1),
       (longlong *******)*local_148 == (longlong *******)0x0)) {
      _Py_Dealloc(local_148);
    }
    local_148 = (longlong *******)0x0;
    if (pppppppplVar17[1] == (longlong *******)PyMethod_Type_exref) {
      pppppppplVar11 = (longlong ********)pppppppplVar17[3];
      pppppppplVar18 = (longlong ********)pppppppplVar17[2];
      if (*(int *)pppppppplVar11 + 1 != 0) {
        *(int *)pppppppplVar11 = *(int *)pppppppplVar11 + 1;
      }
      if (*(int *)pppppppplVar18 + 1 != 0) {
        *(int *)pppppppplVar18 = *(int *)pppppppplVar18 + 1;
      }
      pppppppplVar22 = pppppppplVar13;
      if ((-1 < *(int *)pppppppplVar17) &&
         (*pppppppplVar17 = (longlong *******)((longlong)*pppppppplVar17 + -1),
         *pppppppplVar17 == (longlong *******)0x0)) {
        _Py_Dealloc(pppppppplVar17);
      }
    }
    else {
      pppppppplVar22 = (longlong ********)0x1;
      pppppppplVar11 = pppppppplVar13;
      pppppppplVar18 = pppppppplVar17;
    }
    pcVar21 = (char *)(&local_118 + (longlong)pppppppplVar22);
    local_118 = (longlong *******)pppppppplVar11;
    local_110 = plVar6;
    ppppppplVar5 = (longlong *******)
                   FUN_18000a310((longlong)pppppppplVar18,(undefined8 *)pcVar21,
                                 2U - (longlong)pppppppplVar22 | -(longlong)pppppppplVar22 << 0x3f,0
                                );
    if (((pppppppplVar11 != (longlong ********)0x0) && (-1 < *(int *)pppppppplVar11)) &&
       (*pppppppplVar11 = (longlong *******)((longlong)*pppppppplVar11 + -1),
       *pppppppplVar11 == (longlong *******)0x0)) {
      _Py_Dealloc(pppppppplVar11);
    }
    if ((-1 < (int)*plVar6) && (*plVar6 = *plVar6 + -1, *plVar6 == 0)) {
      _Py_Dealloc(plVar6);
    }
    if ((-1 < *(int *)pppppppplVar18) &&
       (*pppppppplVar18 = (longlong *******)((longlong)*pppppppplVar18 + -1),
       *pppppppplVar18 == (longlong *******)0x0)) {
      _Py_Dealloc(pppppppplVar18);
    }
    pppppppplVar17 = (longlong ********)0x0;
    if (ppppppplVar5 == (longlong *******)0x0) {
      iVar3 = 0x65;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    if (*(int *)ppppppplVar5 + 1 != 0) {
      *(int *)ppppppplVar5 = *(int *)ppppppplVar5 + 1;
    }
    pcVar21 = (char *)&local_70;
    local_68 = 0;
    local_70 = (longlong ******)ppppppplVar5;
    local_res20 = (longlong *)PyObject_VectorcallMethod(DAT_1800169b0,pcVar21,0x8000000000000001,0);
    if ((-1 < *(int *)ppppppplVar5) &&
       (*ppppppplVar5 = (longlong ******)((longlong)*ppppppplVar5 + -1),
       *ppppppplVar5 == (longlong ******)0x0)) {
      _Py_Dealloc(ppppppplVar5);
    }
    pppppppplVar11 = (longlong ********)0x0;
    if ((-1 < *(int *)ppppppplVar5) &&
       (*ppppppplVar5 = (longlong ******)((longlong)*ppppppplVar5 + -1),
       *ppppppplVar5 == (longlong ******)0x0)) {
      _Py_Dealloc(ppppppplVar5);
    }
    if (local_res20 == (longlong *)0x0) {
      iVar3 = 0x65;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    lVar8 = *(longlong *)(local_res20[1] + 0x70);
    if ((lVar8 == 0) || (pcVar14 = *(code **)(lVar8 + 8), pcVar14 == (code *)0x0)) {
      pcVar21 = "\'%.200s\' object is unsliceable";
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"\'%.200s\' object is unsliceable",
                   *(undefined8 *)(local_res20[1] + 0x18));
LAB_180005e5c:
      pppppppplVar22 = (longlong ********)0x0;
      iVar3 = 0x65;
      pppppppplVar18 = (longlong ********)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005e76;
    }
    pcVar21 = (char *)DAT_180016828;
    pppppppplVar18 = (longlong ********)(*pcVar14)(local_res20);
    if (pppppppplVar18 == (longlong ********)0x0) goto LAB_180005e5c;
    if ((-1 < (int)*local_res20) && (*local_res20 = *local_res20 + -1, *local_res20 == 0)) {
      _Py_Dealloc(local_res20);
    }
    pppppppplVar22 = (longlong ********)FUN_18000a140(DAT_180016928);
    local_120 = (longlong *******)pppppppplVar18;
    if (pppppppplVar22 == (longlong ********)0x0) {
      iVar3 = 0x66;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005f30;
    }
    pcVar21 = (char *)pppppppplVar7;
    local_res20 = (longlong *)PyNumber_Add(pppppppplVar22);
    pppppppplVar16 = pppppppplVar13;
    if (local_res20 == (longlong *)0x0) {
      iVar3 = 0x66;
      pppppppplVar18 = (longlong ********)0x0;
      pppppppplVar17 = pppppppplVar13;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005e8c;
    }
    if ((-1 < *(int *)pppppppplVar22) &&
       (*pppppppplVar22 = (longlong *******)((longlong)*pppppppplVar22 + -1),
       *pppppppplVar22 == (longlong *******)0x0)) {
      _Py_Dealloc(pppppppplVar22);
    }
    pcVar21 = (char *)local_58;
    local_60 = 0;
    local_58[0] = (longlong ******)ppppppplVar9;
    pppppppplVar22 =
         (longlong ********)
         FUN_18000a310((longlong)PyBytes_Type_exref,(undefined8 *)pcVar21,0x8000000000000001,0);
    if (pppppppplVar22 == (longlong ********)0x0) {
      iVar3 = 0x66;
      pppppppplVar18 = (longlong ********)0x0;
      pppppppplVar11 = pppppppplVar13;
      pppppppplVar17 = pppppppplVar13;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005e76;
    }
    pcVar21 = (char *)pppppppplVar22;
    pppppppplVar11 = (longlong ********)PyNumber_Add(local_res20);
    if (pppppppplVar11 == (longlong ********)0x0) {
      iVar3 = 0x66;
      pppppppplVar18 = (longlong ********)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005e76;
    }
    if ((-1 < (int)*local_res20) && (*local_res20 = *local_res20 + -1, *local_res20 == 0)) {
      _Py_Dealloc(local_res20);
    }
    if ((-1 < *(int *)pppppppplVar22) &&
       (*pppppppplVar22 = (longlong *******)((longlong)*pppppppplVar22 + -1),
       *pppppppplVar22 == (longlong *******)0x0)) {
      _Py_Dealloc(pppppppplVar22);
    }
    pcVar21 = (char *)pppppppplVar18;
    lVar8 = PyNumber_Add(pppppppplVar11);
    if (lVar8 == 0) {
      iVar3 = 0x66;
      pppppppplVar18 = (longlong ********)0x0;
      puVar19 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180005ec2;
    }
    ppppppplVar5 = (longlong *******)local_108;
    if ((-1 < *(int *)pppppppplVar11) &&
       (*pppppppplVar11 = (longlong *******)((longlong)*pppppppplVar11 + -1),
       *pppppppplVar11 == (longlong *******)0x0)) {
      _Py_Dealloc(pppppppplVar11);
      ppppppplVar5 = (longlong *******)local_108;
    }
  }
  if ((-1 < *(int *)ppppppplVar5) &&
     (*ppppppplVar5 = (longlong ******)((longlong)*ppppppplVar5 + -1),
     *ppppppplVar5 == (longlong ******)0x0)) {
    _Py_Dealloc(ppppppplVar5);
  }
LAB_180005fa5:
  if (((local_138 != (longlong *)0x0) && (-1 < (int)*local_138)) &&
     (*local_138 = *local_138 + -1, *local_138 == 0)) {
    _Py_Dealloc();
  }
  if ((((longlong ********)local_128 != (longlong ********)0x0) && (-1 < *(int *)local_128)) &&
     (*local_128 = (longlong ******)((longlong)*local_128 + -1),
     (longlong *******)*local_128 == (longlong *******)0x0)) {
    _Py_Dealloc(local_128);
  }
  if ((((longlong *******)local_130 != (longlong *******)0x0) && (-1 < *(int *)local_130)) &&
     (*local_130 = (longlong *****)((longlong)*local_130 + -1),
     (longlong ******)*local_130 == (longlong ******)0x0)) {
    _Py_Dealloc();
  }
  if ((((longlong ********)local_140 != (longlong ********)0x0) && (-1 < *(int *)local_140)) &&
     (*local_140 = (longlong ******)((longlong)*local_140 + -1),
     (longlong *******)*local_140 == (longlong *******)0x0)) {
    _Py_Dealloc();
  }
  if ((((longlong ********)local_res18 != (longlong ********)0x0) && (-1 < *(int *)local_res18)) &&
     (*local_res18 = (longlong ******)((longlong)*local_res18 + -1),
     (longlong *******)*local_res18 == (longlong *******)0x0)) {
    _Py_Dealloc(local_res18);
  }
  if (((pppppppplVar18 != (longlong ********)0x0) && (-1 < *(int *)pppppppplVar18)) &&
     (*pppppppplVar18 = (longlong *******)((longlong)*pppppppplVar18 + -1),
     *pppppppplVar18 == (longlong *******)0x0)) {
    _Py_Dealloc(pppppppplVar18);
  }
  return lVar8;
}



// ==== FUN_180006080 @ 180006080 ====

undefined8 FUN_180006080(undefined8 param_1,char *param_2,longlong param_3,longlong param_4)

{
  undefined *puVar1;
  int iVar2;
  longlong lVar3;
  undefined8 extraout_RAX;
  longlong *plVar4;
  longlong *local_res10;
  undefined *local_18;
  undefined8 local_10;
  
  local_res10 = (longlong *)0x0;
  local_18 = &DAT_1800169b8;
  local_10 = 0;
  if (param_4 == 0) {
LAB_180006191:
    if (param_3 == 1) {
      plVar4 = *(longlong **)param_2;
      iVar2 = (int)*plVar4 + 1;
      if (iVar2 != 0) {
        *(int *)plVar4 = iVar2;
      }
      goto LAB_18000621b;
    }
LAB_180006197:
    param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                 "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","decrypt_pyc",
                 "exactly",1,&DAT_180010bad,param_3);
    plVar4 = (longlong *)0x0;
  }
  else {
    lVar3 = *(longlong *)(param_4 + 0x10);
    plVar4 = (longlong *)0x0;
    if (lVar3 < 0) goto LAB_1800061d6;
    if (lVar3 < 1) goto LAB_180006191;
    if (param_3 != 0) {
      if (param_3 != 1) goto LAB_180006197;
      local_res10 = *(longlong **)param_2;
      iVar2 = (int)*local_res10 + 1;
      if (iVar2 != 0) {
        *(int *)local_res10 = iVar2;
      }
    }
    param_2 = param_2 + param_3 * 8;
    lVar3 = FUN_18000ac00(param_4,(undefined8 *)param_2,(longlong *)&local_18,param_4,
                          (longlong)&local_res10,param_3,lVar3,"decrypt_pyc");
    plVar4 = local_res10;
    if (-1 < (int)lVar3) {
      for (; param_3 < 1; param_3 = param_3 + 1) {
        if ((&local_res10)[param_3] == (longlong *)0x0) {
          param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
          PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                       "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","decrypt_pyc",
                       "exactly",1,&DAT_180010bad,param_3);
          plVar4 = local_res10;
          goto LAB_1800061d6;
        }
      }
LAB_18000621b:
      plVar4 = (longlong *)FUN_180006260(param_1,(undefined *)plVar4);
      if (plVar4 == (longlong *)0x0) {
        return extraout_RAX;
      }
      if ((int)*plVar4 < 0) {
        return extraout_RAX;
      }
      *plVar4 = *plVar4 + -1;
      if (*plVar4 != 0) {
        return extraout_RAX;
      }
      _Py_Dealloc(plVar4);
      return extraout_RAX;
    }
  }
LAB_1800061d6:
  puVar1 = PTR_s__security_crypto_py_180011d38;
  if (((plVar4 != (longlong *)0x0) && (-1 < (int)*plVar4)) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)
     ) {
    _Py_Dealloc(plVar4);
  }
  FUN_18000d220("_security_crypto.decrypt_pyc",param_2,0x69,puVar1);
  return 0;
}



// ==== FUN_180006260 @ 180006260 ====

/* WARNING: Type propagation algorithm not settling */

undefined * FUN_180006260(undefined8 param_1,undefined *param_2)

{
  code *pcVar1;
  longlong ****pppplVar2;
  uint uVar3;
  int iVar4;
  longlong lVar5;
  longlong *******ppppppplVar6;
  longlong *******ppppppplVar7;
  longlong *******ppppppplVar8;
  longlong *******ppppppplVar9;
  longlong *plVar10;
  longlong *plVar11;
  longlong *******ppppppplVar12;
  longlong *plVar13;
  longlong *******ppppppplVar14;
  longlong *******ppppppplVar15;
  longlong ******pppppplVar16;
  longlong *******ppppppplVar17;
  undefined *puVar18;
  ulonglong uVar19;
  char *pcVar20;
  undefined *unaff_RBX;
  longlong *****ppppplVar21;
  longlong *******ppppppplVar22;
  longlong *******ppppppplVar23;
  longlong *plVar24;
  bool bVar25;
  longlong *******local_res8;
  longlong *local_res10;
  longlong *******local_res18;
  longlong *******local_res20;
  longlong *local_130;
  longlong *local_128;
  longlong *******local_120;
  longlong *local_118;
  longlong *******local_110;
  longlong *******local_108;
  longlong *******local_100;
  longlong *******local_e0;
  longlong ******local_d8 [3];
  longlong *local_c0;
  longlong ******local_b8;
  undefined8 local_b0;
  undefined8 local_a8;
  longlong ******local_a0;
  longlong *******local_98;
  longlong *local_90;
  longlong ******local_88;
  undefined8 local_80;
  undefined8 local_78;
  longlong ******local_70;
  longlong ******local_68;
  longlong *local_60;
  longlong ******local_58;
  undefined8 local_50;
  
  ppppppplVar17 = (longlong *******)0x0;
  local_120 = (longlong *******)0x0;
  uVar3 = (uint)((code *)param_2 == _Py_TrueStruct_exref);
  local_108 = (longlong *******)0x0;
  local_100 = (longlong *******)0x0;
  local_130 = (longlong *)0x0;
  local_128 = (longlong *)0x0;
  ppppppplVar22 = (longlong *******)0x0;
  local_110 = (longlong *******)0x0;
  local_res18 = (longlong *******)0x0;
  local_res20 = (longlong *******)0x0;
  local_res10 = (longlong *)0x0;
  ppppppplVar23 = (longlong *******)0x0;
  local_res8 = (longlong *******)0x0;
  if (((code *)param_2 != _Py_FalseStruct_exref && (code *)param_2 != _Py_NoneStruct_exref) &&
      (code *)param_2 != _Py_TrueStruct_exref) {
    uVar3 = PyObject_IsTrue(param_2);
  }
  pcVar20 = (char *)_Py_NoneStruct_exref;
  if ((int)uVar3 < 0) {
    iVar4 = 0x6b;
    puVar18 = PTR_s__security_crypto_py_180011d38;
    goto LAB_1800073fc;
  }
  bVar25 = uVar3 == 0;
  if (uVar3 != 0) {
    lVar5 = PyObject_Size(param_2);
    if (lVar5 == -1) {
      iVar4 = 0x6b;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800073fc;
    }
    bVar25 = lVar5 < 0x24;
  }
  if (bVar25) {
    if (*(int *)_Py_NoneStruct_exref + 1 == 0) {
      return unaff_RBX;
    }
    *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
    return unaff_RBX;
  }
  lVar5 = *(longlong *)(*(longlong *)(param_2 + 8) + 0x70);
  if ((lVar5 == 0) || (pcVar1 = *(code **)(lVar5 + 8), pcVar1 == (code *)0x0)) {
    pcVar20 = "\'%.200s\' object is unsliceable";
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"\'%.200s\' object is unsliceable",
                 *(undefined8 *)(*(longlong *)(param_2 + 8) + 0x18));
LAB_1800073f0:
    iVar4 = 0x6d;
    puVar18 = PTR_s__security_crypto_py_180011d38;
LAB_1800073fc:
    FUN_18000d220("_security_crypto.decrypt_pyc",pcVar20,iVar4,puVar18);
    ppppppplVar8 = local_120;
    ppppppplVar15 = local_res20;
    plVar10 = local_130;
    ppppppplVar14 = local_110;
    plVar13 = local_128;
    if (local_120 == (longlong *******)0x0) goto LAB_180007470;
  }
  else {
    pcVar20 = (char *)DAT_180016830;
    local_118 = (longlong *)(*pcVar1)(param_2);
    if (local_118 == (longlong *)0x0) goto LAB_1800073f0;
    ppppppplVar6 = (longlong *******)FUN_18000a140(DAT_180016928);
    if (ppppppplVar6 == (longlong *******)0x0) {
      iVar4 = 0x6d;
      ppppppplVar22 = ppppppplVar17;
      ppppppplVar12 = ppppppplVar17;
      ppppppplVar23 = ppppppplVar17;
      ppppppplVar7 = ppppppplVar17;
LAB_180007087:
      puVar18 = PTR_s__security_crypto_py_180011d38;
      if ((-1 < (int)*local_118) && (*local_118 = *local_118 + -1, *local_118 == 0)) {
        _Py_Dealloc();
      }
LAB_18000723f:
      ppppppplVar15 = ppppppplVar22;
      if (ppppppplVar6 != (longlong *******)0x0) {
LAB_180007244:
        if ((-1 < *(int *)ppppppplVar6) &&
           (*ppppppplVar6 = (longlong ******)((longlong)*ppppppplVar6 + -1),
           *ppppppplVar6 == (longlong ******)0x0)) {
          _Py_Dealloc(ppppppplVar6);
        }
      }
      if (ppppppplVar7 != (longlong *******)0x0) {
LAB_1800072aa:
        if ((-1 < *(int *)ppppppplVar7) &&
           (*ppppppplVar7 = (longlong ******)((longlong)*ppppppplVar7 + -1),
           *ppppppplVar7 == (longlong ******)0x0)) {
          _Py_Dealloc(ppppppplVar7);
        }
      }
      ppppppplVar17 = ppppppplVar23;
      if (ppppppplVar15 != (longlong *******)0x0) {
LAB_1800072c5:
        if ((-1 < *(int *)ppppppplVar15) &&
           (*ppppppplVar15 = (longlong ******)((longlong)*ppppppplVar15 + -1),
           *ppppppplVar15 == (longlong ******)0x0)) {
          _Py_Dealloc(ppppppplVar15);
        }
      }
LAB_1800072f2:
      if (ppppppplVar12 != (longlong *******)0x0) {
LAB_1800072f7:
        if ((-1 < *(int *)ppppppplVar12) &&
           (*ppppppplVar12 = (longlong ******)((longlong)*ppppppplVar12 + -1),
           *ppppppplVar12 == (longlong ******)0x0)) {
          _Py_Dealloc(ppppppplVar12);
        }
      }
      if (((local_res10 != (longlong *)0x0) && (-1 < (int)*local_res10)) &&
         (*local_res10 = *local_res10 + -1, *local_res10 == 0)) {
        _Py_Dealloc();
      }
      if (((ppppppplVar17 != (longlong *******)0x0) && (-1 < *(int *)ppppppplVar17)) &&
         (*ppppppplVar17 = (longlong ******)((longlong)*ppppppplVar17 + -1),
         *ppppppplVar17 == (longlong ******)0x0)) {
        _Py_Dealloc(ppppppplVar17);
      }
      if (((local_res8 != (longlong *******)0x0) && (-1 < *(int *)local_res8)) &&
         (*local_res8 = (longlong ******)((longlong)*local_res8 + -1),
         *local_res8 == (longlong ******)0x0)) {
        _Py_Dealloc();
      }
      goto LAB_1800073fc;
    }
    pcVar20 = (char *)ppppppplVar6;
    ppppppplVar7 = (longlong *******)PyObject_RichCompare(local_118,ppppppplVar6,3);
    if (ppppppplVar7 == (longlong *******)0x0) {
      iVar4 = 0x6d;
      ppppppplVar12 = (longlong *******)0x0;
      goto LAB_180007087;
    }
    if ((-1 < (int)*local_118) && (*local_118 = *local_118 + -1, *local_118 == 0)) {
      _Py_Dealloc(local_118);
    }
    if ((-1 < *(int *)ppppppplVar6) &&
       (*ppppppplVar6 = (longlong ******)((longlong)*ppppppplVar6 + -1),
       *ppppppplVar6 == (longlong ******)0x0)) {
      _Py_Dealloc(ppppppplVar6);
    }
    iVar4 = FUN_18000ef60((undefined *)ppppppplVar7);
    if (iVar4 < 0) {
      iVar4 = 0x6d;
LAB_1800072a3:
      ppppppplVar12 = (longlong *******)0x0;
      ppppppplVar15 = (longlong *******)0x0;
      ppppppplVar23 = ppppppplVar17;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800072aa;
    }
    if ((-1 < *(int *)ppppppplVar7) &&
       (*ppppppplVar7 = (longlong ******)((longlong)*ppppppplVar7 + -1),
       *ppppppplVar7 == (longlong ******)0x0)) {
      _Py_Dealloc(ppppppplVar7);
    }
    if (iVar4 != 0) {
      if (*(int *)_Py_NoneStruct_exref + 1 == 0) {
        return unaff_RBX;
      }
      *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
      return unaff_RBX;
    }
    lVar5 = *(longlong *)(*(longlong *)(param_2 + 8) + 0x70);
    if ((lVar5 == 0) || (pcVar1 = *(code **)(lVar5 + 8), pcVar1 == (code *)0x0)) {
      pcVar20 = "\'%.200s\' object is unsliceable";
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"\'%.200s\' object is unsliceable",
                   *(undefined8 *)(*(longlong *)(param_2 + 8) + 0x18));
LAB_1800073ce:
      iVar4 = 0x6f;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800073fc;
    }
    pcVar20 = (char *)DAT_180016838;
    ppppppplVar8 = (longlong *******)(*pcVar1)(param_2);
    if (ppppppplVar8 == (longlong *******)0x0) goto LAB_1800073ce;
    lVar5 = *(longlong *)(*(longlong *)(param_2 + 8) + 0x70);
    local_120 = ppppppplVar8;
    if ((lVar5 == 0) || (pcVar1 = *(code **)(lVar5 + 8), pcVar1 == (code *)0x0)) {
      pcVar20 = "\'%.200s\' object is unsliceable";
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"\'%.200s\' object is unsliceable",
                   *(undefined8 *)(*(longlong *)(param_2 + 8) + 0x18));
LAB_1800073ac:
      iVar4 = 0x70;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800073fc;
    }
    pcVar20 = (char *)DAT_180016840;
    ppppppplVar22 = (longlong *******)(*pcVar1)(param_2);
    if (ppppppplVar22 == (longlong *******)0x0) goto LAB_1800073ac;
    lVar5 = *(longlong *)(*(longlong *)(param_2 + 8) + 0x70);
    local_108 = ppppppplVar22;
    if ((lVar5 == 0) || (pcVar1 = *(code **)(lVar5 + 8), pcVar1 == (code *)0x0)) {
      pcVar20 = "\'%.200s\' object is unsliceable";
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"\'%.200s\' object is unsliceable",
                   *(undefined8 *)(*(longlong *)(param_2 + 8) + 0x18));
LAB_18000738a:
      iVar4 = 0x71;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800073fc;
    }
    pcVar20 = (char *)DAT_180016848;
    ppppppplVar9 = (longlong *******)(*pcVar1)(param_2);
    if (ppppppplVar9 == (longlong *******)0x0) goto LAB_18000738a;
    ppppplVar21 = (longlong *****)0x0;
    plVar10 = (longlong *)FUN_18000a140(DAT_180016ae0);
    local_100 = ppppppplVar9;
    if (plVar10 == (longlong *)0x0) {
      iVar4 = 0x72;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800073fc;
    }
    lVar5 = 1;
    plVar11 = plVar10;
    if ((code *)plVar10[1] == PyMethod_Type_exref) {
      ppppplVar21 = (longlong *****)plVar10[3];
      plVar11 = (longlong *)plVar10[2];
      if (*(int *)ppppplVar21 + 1 != 0) {
        *(int *)ppppplVar21 = *(int *)ppppplVar21 + 1;
      }
      iVar4 = (int)*plVar11 + 1;
      if (iVar4 != 0) {
        *(int *)plVar11 = iVar4;
      }
      if ((-1 < (int)*plVar10) && (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
        _Py_Dealloc();
      }
      lVar5 = 0;
    }
    local_d8[1] = (longlong ******)0x0;
    pcVar20 = (char *)(local_d8 + lVar5);
    local_d8[0] = (longlong ******)ppppplVar21;
    plVar10 = (longlong *)
              FUN_18000a310((longlong)plVar11,(undefined8 *)pcVar20,1U - lVar5 | -lVar5 << 0x3f,0);
    if (((ppppplVar21 != (longlong *****)0x0) && (-1 < *(int *)ppppplVar21)) &&
       (*ppppplVar21 = (longlong ****)((longlong)*ppppplVar21 + -1),
       *ppppplVar21 == (longlong ****)0x0)) {
      _Py_Dealloc(ppppplVar21);
    }
    if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
      _Py_Dealloc(plVar11);
    }
    if (plVar10 == (longlong *)0x0) {
      iVar4 = 0x72;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800073fc;
    }
    pppppplVar16 = (longlong ******)0x0;
    plVar11 = (longlong *)FUN_18000a140(DAT_180016a08);
    local_130 = plVar10;
    if (plVar11 == (longlong *)0x0) {
      iVar4 = 0x73;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800073fc;
    }
    pcVar20 = (char *)DAT_180016b20;
    if (*(code **)(plVar11[1] + 0x90) == (code *)0x0) {
      ppppppplVar12 = (longlong *******)PyObject_GetAttr(plVar11);
    }
    else {
      ppppppplVar12 = (longlong *******)(**(code **)(plVar11[1] + 0x90))();
    }
    if (ppppppplVar12 == (longlong *******)0x0) {
      iVar4 = 0x73;
LAB_1800072de:
      puVar18 = PTR_s__security_crypto_py_180011d38;
      ppppppplVar17 = (longlong *******)0x0;
      if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
        _Py_Dealloc(plVar11);
      }
      goto LAB_1800072f2;
    }
    if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
      _Py_Dealloc(plVar11);
    }
    pcVar20 = (char *)ppppppplVar9;
    plVar11 = (longlong *)PyNumber_Add(plVar10);
    if (plVar11 == (longlong *)0x0) {
      iVar4 = 0x73;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800072f7;
    }
    lVar5 = 1;
    ppppppplVar6 = ppppppplVar12;
    if (ppppppplVar12[1] == (longlong ******)PyMethod_Type_exref) {
      pppppplVar16 = ppppppplVar12[3];
      ppppppplVar6 = (longlong *******)ppppppplVar12[2];
      if (*(int *)pppppplVar16 + 1 != 0) {
        *(int *)pppppplVar16 = *(int *)pppppplVar16 + 1;
      }
      if (*(int *)ppppppplVar6 + 1 != 0) {
        *(int *)ppppppplVar6 = *(int *)ppppppplVar6 + 1;
      }
      if ((-1 < *(int *)ppppppplVar12) &&
         (*ppppppplVar12 = (longlong ******)((longlong)*ppppppplVar12 + -1),
         *ppppppplVar12 == (longlong ******)0x0)) {
        _Py_Dealloc();
      }
      lVar5 = 0;
    }
    pcVar20 = (char *)(local_d8 + lVar5 + 2);
    local_d8[2] = pppppplVar16;
    local_c0 = plVar11;
    plVar13 = (longlong *)
              FUN_18000a310((longlong)ppppppplVar6,(undefined8 *)pcVar20,2U - lVar5 | -lVar5 << 0x3f
                            ,0);
    if (((pppppplVar16 != (longlong ******)0x0) && (-1 < *(int *)pppppplVar16)) &&
       (*pppppplVar16 = (longlong *****)((longlong)*pppppplVar16 + -1),
       *pppppplVar16 == (longlong *****)0x0)) {
      _Py_Dealloc(pppppplVar16);
    }
    ppppppplVar15 = (longlong *******)0x0;
    if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
      _Py_Dealloc(plVar11);
    }
    if ((-1 < *(int *)ppppppplVar6) &&
       (*ppppppplVar6 = (longlong ******)((longlong)*ppppppplVar6 + -1),
       *ppppppplVar6 == (longlong ******)0x0)) {
      _Py_Dealloc(ppppppplVar6);
    }
    ppppppplVar12 = (longlong *******)0x0;
    if (plVar13 == (longlong *)0x0) {
      iVar4 = 0x73;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800073fc;
    }
    iVar4 = (int)*plVar13 + 1;
    if (iVar4 != 0) {
      *(int *)plVar13 = iVar4;
    }
    pcVar20 = (char *)(local_d8 + 4);
    local_b0 = 0;
    local_b8 = (longlong ******)plVar13;
    ppppppplVar7 = (longlong *******)
                   PyObject_VectorcallMethod(DAT_1800169b0,pcVar20,0x8000000000000001,0);
    if (-1 < (int)*plVar13) {
      *plVar13 = *plVar13 + -1;
      if (*plVar13 == 0) {
        _Py_Dealloc(plVar13);
      }
      if ((-1 < (int)*plVar13) && (*plVar13 = *plVar13 + -1, *plVar13 == 0)) {
        _Py_Dealloc(plVar13);
      }
    }
    if (ppppppplVar7 == (longlong *******)0x0) {
      iVar4 = 0x73;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800073fc;
    }
    ppppplVar21 = ppppppplVar7[1][0xe];
    if ((ppppplVar21 == (longlong *****)0x0) ||
       (pppplVar2 = ppppplVar21[1], pppplVar2 == (longlong ****)0x0)) {
      pcVar20 = "\'%.200s\' object is unsliceable";
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"\'%.200s\' object is unsliceable",
                   ppppppplVar7[1][3]);
LAB_18000729e:
      iVar4 = 0x73;
      goto LAB_1800072a3;
    }
    pcVar20 = (char *)DAT_180016828;
    plVar13 = (longlong *)(*(code *)pppplVar2)(ppppppplVar7);
    if (plVar13 == (longlong *)0x0) goto LAB_18000729e;
    if ((-1 < *(int *)ppppppplVar7) &&
       (*ppppppplVar7 = (longlong ******)((longlong)*ppppppplVar7 + -1),
       *ppppppplVar7 == (longlong ******)0x0)) {
      _Py_Dealloc(ppppppplVar7);
    }
    ppppppplVar7 = (longlong *******)0x0;
    pcVar20 = (char *)ppppppplVar22;
    ppppppplVar6 = (longlong *******)PyObject_RichCompare(plVar13,ppppppplVar22,3);
    local_128 = plVar13;
    if (ppppppplVar6 == (longlong *******)0x0) {
      iVar4 = 0x74;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800073fc;
    }
    iVar4 = FUN_18000ef60((undefined *)ppppppplVar6);
    if (iVar4 < 0) {
      iVar4 = 0x74;
      ppppppplVar23 = ppppppplVar17;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_180007244;
    }
    if ((-1 < *(int *)ppppppplVar6) &&
       (*ppppppplVar6 = (longlong ******)((longlong)*ppppppplVar6 + -1),
       *ppppppplVar6 == (longlong ******)0x0)) {
      _Py_Dealloc(ppppppplVar6);
    }
    if (iVar4 == 0) {
      lVar5 = PyObject_Size(ppppppplVar9);
      if (lVar5 == -1) {
        iVar4 = 0x76;
        puVar18 = PTR_s__security_crypto_py_180011d38;
        goto LAB_1800073fc;
      }
      plVar11 = (longlong *)PyLong_FromSsize_t(lVar5);
      if (plVar11 == (longlong *)0x0) {
        iVar4 = 0x76;
        puVar18 = PTR_s__security_crypto_py_180011d38;
        goto LAB_1800073fc;
      }
      pcVar20 = (char *)(local_d8 + 7);
      local_a8 = 0;
      local_a0 = (longlong ******)plVar11;
      ppppppplVar14 =
           (longlong *******)
           FUN_18000a310((longlong)PyByteArray_Type_exref,(undefined8 *)pcVar20,0x8000000000000001,0
                        );
      if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
        _Py_Dealloc(plVar11);
      }
      if (ppppppplVar14 == (longlong *******)0x0) {
        iVar4 = 0x76;
        puVar18 = PTR_s__security_crypto_py_180011d38;
        goto LAB_1800073fc;
      }
      plVar11 = (longlong *)FUN_18000a140(DAT_180016a08);
      local_110 = ppppppplVar14;
      if (plVar11 == (longlong *)0x0) {
        iVar4 = 0x77;
        puVar18 = PTR_s__security_crypto_py_180011d38;
        goto LAB_1800073fc;
      }
      pcVar20 = (char *)DAT_180016b20;
      if (*(code **)(plVar11[1] + 0x90) == (code *)0x0) {
        ppppppplVar15 = (longlong *******)PyObject_GetAttr(plVar11);
      }
      else {
        ppppppplVar15 = (longlong *******)(**(code **)(plVar11[1] + 0x90))();
      }
      if (ppppppplVar15 == (longlong *******)0x0) {
        iVar4 = 0x77;
        goto LAB_1800072de;
      }
      if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
        _Py_Dealloc(plVar11);
      }
      pcVar20 = (char *)ppppppplVar8;
      plVar11 = (longlong *)PyNumber_Add(plVar10);
      if (plVar11 != (longlong *)0x0) {
        lVar5 = 1;
        ppppppplVar22 = ppppppplVar15;
        if (ppppppplVar15[1] == (longlong ******)PyMethod_Type_exref) {
          ppppppplVar12 = (longlong *******)ppppppplVar15[3];
          ppppppplVar22 = (longlong *******)ppppppplVar15[2];
          if (*(int *)ppppppplVar12 + 1 != 0) {
            *(int *)ppppppplVar12 = *(int *)ppppppplVar12 + 1;
          }
          if (*(int *)ppppppplVar22 + 1 != 0) {
            *(int *)ppppppplVar22 = *(int *)ppppppplVar22 + 1;
          }
          if ((-1 < *(int *)ppppppplVar15) &&
             (*ppppppplVar15 = (longlong ******)((longlong)*ppppppplVar15 + -1),
             *ppppppplVar15 == (longlong ******)0x0)) {
            _Py_Dealloc();
          }
          lVar5 = 0;
        }
        pcVar20 = (char *)(&local_98 + lVar5);
        local_98 = ppppppplVar12;
        local_90 = plVar11;
        pppppplVar16 = (longlong ******)
                       FUN_18000a310((longlong)ppppppplVar22,(undefined8 *)pcVar20,
                                     2U - lVar5 | -lVar5 << 0x3f,0);
        if (((ppppppplVar12 != (longlong *******)0x0) && (-1 < *(int *)ppppppplVar12)) &&
           (*ppppppplVar12 = (longlong ******)((longlong)*ppppppplVar12 + -1),
           *ppppppplVar12 == (longlong ******)0x0)) {
          _Py_Dealloc(ppppppplVar12);
        }
        ppppppplVar12 = (longlong *******)0x0;
        if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
          _Py_Dealloc(plVar11);
        }
        if ((-1 < *(int *)ppppppplVar22) &&
           (*ppppppplVar22 = (longlong ******)((longlong)*ppppppplVar22 + -1),
           *ppppppplVar22 == (longlong ******)0x0)) {
          _Py_Dealloc(ppppppplVar22);
        }
        ppppppplVar15 = (longlong *******)0x0;
        if (pppppplVar16 == (longlong ******)0x0) {
          iVar4 = 0x77;
          puVar18 = PTR_s__security_crypto_py_180011d38;
          goto LAB_1800073fc;
        }
        if (*(int *)pppppplVar16 + 1 != 0) {
          *(int *)pppppplVar16 = *(int *)pppppplVar16 + 1;
        }
        pcVar20 = (char *)&local_88;
        local_80 = 0;
        local_88 = pppppplVar16;
        ppppppplVar22 =
             (longlong *******)PyObject_VectorcallMethod(DAT_1800169b0,pcVar20,0x8000000000000001);
        if (-1 < *(int *)pppppplVar16) {
          *pppppplVar16 = (longlong *****)((longlong)*pppppplVar16 + -1);
          if (*pppppplVar16 == (longlong *****)0x0) {
            _Py_Dealloc(pppppplVar16);
          }
          if ((-1 < *(int *)pppppplVar16) &&
             (*pppppplVar16 = (longlong *****)((longlong)*pppppplVar16 + -1),
             *pppppplVar16 == (longlong *****)0x0)) {
            _Py_Dealloc(pppppplVar16);
          }
        }
        if (ppppppplVar22 == (longlong *******)0x0) {
          iVar4 = 0x77;
          puVar18 = PTR_s__security_crypto_py_180011d38;
          goto LAB_1800073fc;
        }
        lVar5 = PyObject_Size(ppppppplVar9);
        local_res18 = ppppppplVar22;
        if (lVar5 == -1) {
          iVar4 = 0x78;
          puVar18 = PTR_s__security_crypto_py_180011d38;
          goto LAB_1800073fc;
        }
        pppppplVar16 = (longlong ******)PyLong_FromSsize_t(lVar5);
        if (pppppplVar16 == (longlong ******)0x0) {
          iVar4 = 0x78;
          puVar18 = PTR_s__security_crypto_py_180011d38;
          goto LAB_1800073fc;
        }
        pcVar20 = (char *)&local_70;
        local_78 = 0;
        local_70 = pppppplVar16;
        ppppppplVar6 = (longlong *******)
                       FUN_18000a310((longlong)PyRange_Type_exref,(undefined8 *)pcVar20,
                                     0x8000000000000001,0);
        ppppppplVar7 = (longlong *******)0x0;
        if ((-1 < *(int *)pppppplVar16) &&
           (*pppppplVar16 = (longlong *****)((longlong)*pppppplVar16 + -1),
           *pppppplVar16 == (longlong *****)0x0)) {
          _Py_Dealloc(pppppplVar16);
        }
        if (ppppppplVar6 == (longlong *******)0x0) {
          iVar4 = 0x78;
          puVar18 = PTR_s__security_crypto_py_180011d38;
          goto LAB_1800073fc;
        }
        local_118 = (longlong *)PyObject_GetIter(ppppppplVar6);
        if (local_118 == (longlong *)0x0) {
          iVar4 = 0x78;
          puVar18 = PTR_s__security_crypto_py_180011d38;
          goto LAB_180007244;
        }
        pcVar1 = *(code **)(local_118[1] + 0xe0);
        if (pcVar1 == (code *)0x0) {
LAB_180007082:
          local_res10 = (longlong *)0x0;
          local_res8 = (longlong *******)0x0;
          ppppppplVar7 = (longlong *******)0x0;
          ppppppplVar22 = (longlong *******)0x0;
          iVar4 = 0x78;
          ppppppplVar12 = (longlong *******)0x0;
          ppppppplVar23 = (longlong *******)0x0;
          goto LAB_180007087;
        }
        if ((-1 < *(int *)ppppppplVar6) &&
           (*ppppppplVar6 = (longlong ******)((longlong)*ppppppplVar6 + -1),
           *ppppppplVar6 == (longlong ******)0x0)) {
          _Py_Dealloc(ppppppplVar6);
        }
        ppppppplVar23 = (longlong *******)(*pcVar1)(local_118);
        while (local_res20 = ppppppplVar23, local_res20 != (longlong *******)0x0) {
          if (((ppppppplVar15 != (longlong *******)0x0) && (-1 < *(int *)ppppppplVar15)) &&
             (*ppppppplVar15 = (longlong ******)((longlong)*ppppppplVar15 + -1),
             *ppppppplVar15 == (longlong ******)0x0)) {
            _Py_Dealloc();
          }
          ppppppplVar6 = (longlong *******)PyObject_RichCompare(local_res20);
          if ((ppppppplVar6 == (longlong *******)0x0) ||
             (iVar4 = FUN_18000ef60((undefined *)ppppppplVar6), iVar4 < 0)) {
            pcVar20 = (char *)0x0;
            ppppppplVar7 = (longlong *******)0x0;
            ppppppplVar22 = (longlong *******)0x0;
            local_res10 = (longlong *)0x0;
            ppppppplVar12 = (longlong *******)0x0;
            ppppppplVar23 = (longlong *******)0x0;
            iVar4 = 0x79;
            local_res8 = (longlong *******)0x0;
            goto LAB_180007087;
          }
          if ((-1 < *(int *)ppppppplVar6) &&
             (*ppppppplVar6 = (longlong ******)((longlong)*ppppppplVar6 + -1),
             *ppppppplVar6 == (longlong ******)0x0)) {
            _Py_Dealloc(ppppppplVar6);
          }
          ppppppplVar17 = local_res18;
          if (iVar4 != 0) {
            pcVar20 = (char *)DAT_180016c60;
            ppppppplVar6 = (longlong *******)FUN_18000b6b0((int *)local_res20,DAT_180016c60);
            if (ppppppplVar6 == (longlong *******)0x0) {
              ppppppplVar22 = (longlong *******)0x0;
              ppppppplVar7 = (longlong *******)0x0;
              ppppppplVar12 = (longlong *******)0x0;
              local_res10 = (longlong *)0x0;
              ppppppplVar23 = (longlong *******)0x0;
              iVar4 = 0x79;
              local_res8 = (longlong *******)0x0;
              goto LAB_180007087;
            }
            pcVar20 = (char *)DAT_180016c20;
            uVar3 = FUN_18000b7a0((longlong)ppppppplVar6,(longlong)DAT_180016c20);
            if ((int)uVar3 < 0) {
              iVar4 = 0x79;
              ppppppplVar7 = (longlong *******)0x0;
              local_res10 = (longlong *)0x0;
              ppppppplVar22 = (longlong *******)0x0;
              local_res8 = (longlong *******)0x0;
              ppppppplVar12 = (longlong *******)0x0;
              ppppppplVar23 = (longlong *******)0x0;
              goto LAB_180007087;
            }
            if ((-1 < *(int *)ppppppplVar6) &&
               (*ppppppplVar6 = (longlong ******)((longlong)*ppppppplVar6 + -1),
               *ppppppplVar6 == (longlong ******)0x0)) {
              _Py_Dealloc(ppppppplVar6);
            }
            ppppppplVar7 = (longlong *******)0x0;
            if (uVar3 != 0) {
              ppppplVar21 = (longlong *****)0x0;
              ppppppplVar6 = (longlong *******)0x0;
              ppppppplVar12 = (longlong *******)FUN_18000a140(DAT_180016a08);
              if (ppppppplVar12 == (longlong *******)0x0) {
                ppppppplVar22 = (longlong *******)0x0;
                iVar4 = 0x7a;
                local_res10 = (longlong *)0x0;
                ppppppplVar23 = (longlong *******)0x0;
                local_res8 = (longlong *******)0x0;
              }
              else {
                pcVar20 = (char *)DAT_180016b20;
                if (ppppppplVar12[1][0x12] == (longlong *****)0x0) {
                  local_res10 = (longlong *)PyObject_GetAttr(ppppppplVar12);
                }
                else {
                  local_res10 = (longlong *)(*(code *)ppppppplVar12[1][0x12])();
                }
                if (local_res10 != (longlong *)0x0) {
                  if ((-1 < *(int *)ppppppplVar12) &&
                     (*ppppppplVar12 = (longlong ******)((longlong)*ppppppplVar12 + -1),
                     *ppppppplVar12 == (longlong ******)0x0)) {
                    _Py_Dealloc(ppppppplVar12);
                  }
                  pcVar20 = (char *)ppppppplVar8;
                  ppppppplVar12 = (longlong *******)PyNumber_Add(plVar10);
                  if (ppppppplVar12 != (longlong *******)0x0) {
                    pcVar20 = (char *)DAT_180016b50;
                    if (local_res20[1][0x12] == (longlong *****)0x0) {
                      ppppppplVar23 = (longlong *******)PyObject_GetAttr(local_res20);
                    }
                    else {
                      ppppppplVar23 = (longlong *******)(*(code *)local_res20[1][0x12])();
                    }
                    if (ppppppplVar23 == (longlong *******)0x0) {
                      ppppppplVar7 = (longlong *******)0x0;
                      iVar4 = 0x7a;
                      ppppppplVar22 = (longlong *******)0x0;
                      local_res8 = (longlong *******)0x0;
                    }
                    else {
                      pcVar20 = (char *)DAT_180016850;
                      local_res8 = (longlong *******)
                                   FUN_18000a1d0((longlong)ppppppplVar23,DAT_180016850,0);
                      if (local_res8 != (longlong *******)0x0) {
                        if ((-1 < *(int *)ppppppplVar23) &&
                           (*ppppppplVar23 = (longlong ******)((longlong)*ppppppplVar23 + -1),
                           *ppppppplVar23 == (longlong ******)0x0)) {
                          _Py_Dealloc(ppppppplVar23);
                        }
                        pcVar20 = (char *)local_res8;
                        plVar11 = (longlong *)PyNumber_Add(ppppppplVar12);
                        ppppppplVar23 = (longlong *******)0x0;
                        if (plVar11 != (longlong *)0x0) {
                          if ((-1 < *(int *)ppppppplVar12) &&
                             (*ppppppplVar12 = (longlong ******)((longlong)*ppppppplVar12 + -1),
                             *ppppppplVar12 == (longlong ******)0x0)) {
                            _Py_Dealloc(ppppppplVar12);
                          }
                          ppppppplVar12 = (longlong *******)0x0;
                          if ((-1 < *(int *)local_res8) &&
                             (*local_res8 = (longlong ******)((longlong)*local_res8 + -1),
                             *local_res8 == (longlong ******)0x0)) {
                            _Py_Dealloc();
                          }
                          lVar5 = 1;
                          local_res8 = (longlong *******)0x0;
                          plVar24 = local_res10;
                          if ((code *)local_res10[1] == PyMethod_Type_exref) {
                            ppppplVar21 = (longlong *****)local_res10[3];
                            plVar24 = (longlong *)local_res10[2];
                            if (*(int *)ppppplVar21 + 1 != 0) {
                              *(int *)ppppplVar21 = *(int *)ppppplVar21 + 1;
                            }
                            iVar4 = (int)*plVar24 + 1;
                            if (iVar4 != 0) {
                              *(int *)plVar24 = iVar4;
                            }
                            if ((-1 < (int)*local_res10) &&
                               (*local_res10 = *local_res10 + -1, *local_res10 == 0)) {
                              _Py_Dealloc();
                            }
                            lVar5 = 0;
                          }
                          pcVar20 = (char *)(&local_68 + lVar5);
                          local_68 = (longlong ******)ppppplVar21;
                          local_60 = plVar11;
                          pppppplVar16 = (longlong ******)
                                         FUN_18000a310((longlong)plVar24,(undefined8 *)pcVar20,
                                                       2U - lVar5 | -lVar5 << 0x3f,0);
                          if (((ppppplVar21 != (longlong *****)0x0) && (-1 < *(int *)ppppplVar21))
                             && (*ppppplVar21 = (longlong ****)((longlong)*ppppplVar21 + -1),
                                *ppppplVar21 == (longlong ****)0x0)) {
                            _Py_Dealloc(ppppplVar21);
                          }
                          if ((-1 < (int)*plVar11) && (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
                            _Py_Dealloc(plVar11);
                          }
                          ppppppplVar23 = (longlong *******)0x0;
                          if ((-1 < (int)*plVar24) && (*plVar24 = *plVar24 + -1, *plVar24 == 0)) {
                            _Py_Dealloc(plVar24);
                          }
                          local_res10 = (longlong *)0x0;
                          if (pppppplVar16 == (longlong ******)0x0) {
                            ppppppplVar6 = (longlong *******)0x0;
                            iVar4 = 0x7a;
                            ppppppplVar7 = (longlong *******)0x0;
                            ppppppplVar22 = (longlong *******)0x0;
                          }
                          else {
                            if (*(int *)pppppplVar16 + 1 != 0) {
                              *(int *)pppppplVar16 = *(int *)pppppplVar16 + 1;
                            }
                            pcVar20 = (char *)&local_58;
                            local_50 = 0;
                            local_58 = pppppplVar16;
                            ppppppplVar17 =
                                 (longlong *******)
                                 PyObject_VectorcallMethod(DAT_1800169b0,pcVar20,0x8000000000000001)
                            ;
                            if ((-1 < *(int *)pppppplVar16) &&
                               (*pppppplVar16 = (longlong *****)((longlong)*pppppplVar16 + -1),
                               *pppppplVar16 == (longlong *****)0x0)) {
                              _Py_Dealloc(pppppplVar16);
                            }
                            ppppppplVar7 = (longlong *******)0x0;
                            if ((-1 < *(int *)pppppplVar16) &&
                               (*pppppplVar16 = (longlong *****)((longlong)*pppppplVar16 + -1),
                               *pppppplVar16 == (longlong *****)0x0)) {
                              _Py_Dealloc(pppppplVar16);
                            }
                            ppppppplVar22 = (longlong *******)0x0;
                            if (ppppppplVar17 != (longlong *******)0x0) {
                              if ((-1 < *(int *)local_res18) &&
                                 (*local_res18 = (longlong ******)((longlong)*local_res18 + -1),
                                 *local_res18 == (longlong ******)0x0)) {
                                _Py_Dealloc(local_res18);
                              }
                              goto LAB_180006f4e;
                            }
                            iVar4 = 0x7a;
                            ppppppplVar6 = (longlong *******)0x0;
                          }
                          goto LAB_180007087;
                        }
                      }
                      ppppppplVar7 = (longlong *******)0x0;
                      iVar4 = 0x7a;
                      ppppppplVar22 = (longlong *******)0x0;
                    }
                    goto LAB_180007087;
                  }
                }
                ppppppplVar22 = (longlong *******)0x0;
                ppppppplVar7 = (longlong *******)0x0;
                ppppppplVar23 = (longlong *******)0x0;
                local_res8 = (longlong *******)0x0;
                iVar4 = 0x7a;
              }
              goto LAB_180007087;
            }
          }
LAB_180006f4e:
          local_res18 = ppppppplVar17;
          ppppppplVar7 = (longlong *******)0x0;
          local_res8 = (longlong *******)0x0;
          pcVar20 = (char *)local_res20;
          ppppppplVar6 = (longlong *******)
                         FUN_18000af90((longlong)ppppppplVar9,(longlong)local_res20);
          if (ppppppplVar6 == (longlong *******)0x0) {
            iVar4 = 0x7b;
            local_res10 = (longlong *)0x0;
            ppppppplVar22 = (longlong *******)0x0;
            local_res8 = (longlong *******)0x0;
            ppppppplVar12 = (longlong *******)0x0;
            ppppppplVar23 = (longlong *******)0x0;
            goto LAB_180007087;
          }
          pcVar20 = (char *)DAT_180016c60;
          ppppppplVar22 = (longlong *******)FUN_18000b6b0((int *)local_res20,DAT_180016c60);
          if (ppppppplVar22 == (longlong *******)0x0) {
            iVar4 = 0x7b;
            local_res10 = (longlong *)0x0;
            ppppppplVar12 = (longlong *******)0x0;
            local_res8 = (longlong *******)0x0;
            ppppppplVar23 = (longlong *******)0x0;
            goto LAB_180007087;
          }
          pcVar20 = (char *)ppppppplVar22;
          ppppppplVar7 = (longlong *******)
                         FUN_18000af90((longlong)local_res18,(longlong)ppppppplVar22);
          ppppppplVar12 = local_res8;
          ppppppplVar23 = local_res8;
          if (ppppppplVar7 == (longlong *******)0x0) {
LAB_18000715f:
            iVar4 = 0x7b;
            local_res10 = (longlong *)0x0;
            goto LAB_180007087;
          }
          if ((-1 < *(int *)ppppppplVar22) &&
             (*ppppppplVar22 = (longlong ******)((longlong)*ppppppplVar22 + -1),
             *ppppppplVar22 == (longlong ******)0x0)) {
            _Py_Dealloc(ppppppplVar22);
          }
          pcVar20 = (char *)ppppppplVar7;
          ppppppplVar22 = (longlong *******)PyNumber_Xor(ppppppplVar6);
          if (ppppppplVar22 == (longlong *******)0x0) goto LAB_18000715f;
          if ((-1 < *(int *)ppppppplVar6) &&
             (*ppppppplVar6 = (longlong ******)((longlong)*ppppppplVar6 + -1),
             *ppppppplVar6 == (longlong ******)0x0)) {
            _Py_Dealloc(ppppppplVar6);
          }
          ppppppplVar6 = (longlong *******)0x0;
          if ((-1 < *(int *)ppppppplVar7) &&
             (*ppppppplVar7 = (longlong ******)((longlong)*ppppppplVar7 + -1),
             *ppppppplVar7 == (longlong ******)0x0)) {
            _Py_Dealloc(ppppppplVar7);
          }
          ppppppplVar7 = (longlong *******)0x0;
          pcVar20 = (char *)local_res20;
          iVar4 = PyObject_SetItem(ppppppplVar14,local_res20,ppppppplVar22);
          if (iVar4 < 0) {
            local_res10 = (longlong *)0x0;
            iVar4 = 0x7b;
            goto LAB_180007087;
          }
          if ((-1 < *(int *)ppppppplVar22) &&
             (*ppppppplVar22 = (longlong ******)((longlong)*ppppppplVar22 + -1),
             *ppppppplVar22 == (longlong ******)0x0)) {
            _Py_Dealloc(ppppppplVar22);
          }
          ppppppplVar23 = (longlong *******)(*pcVar1)(local_118);
          ppppppplVar15 = local_res20;
        }
        ppppppplVar6 = (longlong *******)0x0;
        puVar18 = (undefined *)PyErr_Occurred();
        local_res20 = ppppppplVar15;
        if (puVar18 != (undefined *)0x0) {
          uVar19 = FUN_18000d500(puVar18,*(undefined **)PyExc_StopIteration_exref);
          if ((int)uVar19 == 0) {
            pcVar20 = (char *)0x0;
            goto LAB_180007082;
          }
          PyErr_Clear();
        }
        if ((-1 < (int)*local_118) && (*local_118 = *local_118 + -1, *local_118 == 0)) {
          _Py_Dealloc(local_118);
        }
        local_e0 = ppppppplVar14;
        lVar5 = FUN_18000a310((longlong)PyBytes_Type_exref,&local_e0,0x8000000000000001,0);
        ppppppplVar22 = (longlong *******)0x0;
        if (lVar5 != 0) goto LAB_18000745f;
        pcVar20 = (char *)0x0;
        ppppppplVar7 = (longlong *******)0x0;
        local_res10 = (longlong *)0x0;
        ppppppplVar12 = (longlong *******)0x0;
        ppppppplVar23 = (longlong *******)0x0;
        iVar4 = 0x7c;
        local_res8 = (longlong *******)0x0;
        puVar18 = PTR_s__security_crypto_py_180011d38;
        goto LAB_18000723f;
      }
      iVar4 = 0x77;
      puVar18 = PTR_s__security_crypto_py_180011d38;
      goto LAB_1800072c5;
    }
    local_res18 = ppppppplVar15;
    ppppppplVar14 = ppppppplVar15;
    if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
      *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
      local_res18 = (longlong *******)0x0;
      ppppppplVar14 = (longlong *******)0x0;
    }
  }
LAB_18000745f:
  if ((-1 < *(int *)ppppppplVar8) &&
     (*ppppppplVar8 = (longlong ******)((longlong)*ppppppplVar8 + -1),
     *ppppppplVar8 == (longlong ******)0x0)) {
    _Py_Dealloc();
  }
LAB_180007470:
  if (((local_108 != (longlong *******)0x0) && (-1 < *(int *)local_108)) &&
     (*local_108 = (longlong ******)((longlong)*local_108 + -1), *local_108 == (longlong ******)0x0)
     ) {
    _Py_Dealloc();
  }
  if (((local_100 != (longlong *******)0x0) && (-1 < *(int *)local_100)) &&
     (*local_100 = (longlong ******)((longlong)*local_100 + -1), *local_100 == (longlong ******)0x0)
     ) {
    _Py_Dealloc();
  }
  if (((plVar10 != (longlong *)0x0) && (-1 < (int)*plVar10)) &&
     (*plVar10 = *plVar10 + -1, *plVar10 == 0)) {
    _Py_Dealloc(plVar10);
  }
  if (((plVar13 != (longlong *)0x0) && (-1 < (int)*plVar13)) &&
     (*plVar13 = *plVar13 + -1, *plVar13 == 0)) {
    _Py_Dealloc(plVar13);
  }
  if (((ppppppplVar14 != (longlong *******)0x0) && (-1 < *(int *)ppppppplVar14)) &&
     (*ppppppplVar14 = (longlong ******)((longlong)*ppppppplVar14 + -1),
     *ppppppplVar14 == (longlong ******)0x0)) {
    _Py_Dealloc(ppppppplVar14);
  }
  if (((local_res18 != (longlong *******)0x0) && (-1 < *(int *)local_res18)) &&
     (*local_res18 = (longlong ******)((longlong)*local_res18 + -1),
     *local_res18 == (longlong ******)0x0)) {
    _Py_Dealloc(local_res18);
  }
  if (((ppppppplVar15 != (longlong *******)0x0) && (-1 < *(int *)ppppppplVar15)) &&
     (*ppppppplVar15 = (longlong ******)((longlong)*ppppppplVar15 + -1),
     *ppppppplVar15 == (longlong ******)0x0)) {
    _Py_Dealloc(ppppppplVar15);
  }
  return unaff_RBX;
}



// ==== FUN_180007550 @ 180007550 ====

undefined * FUN_180007550(longlong param_1,char *param_2,longlong param_3,longlong param_4)

{
  int iVar1;
  longlong lVar2;
  undefined *puVar3;
  longlong *plVar4;
  longlong *local_res10;
  undefined *local_18;
  undefined8 local_10;
  
  local_res10 = (longlong *)0x0;
  local_18 = &DAT_180016978;
  local_10 = 0;
  if (param_4 == 0) {
LAB_18000765c:
    if (param_3 == 1) {
      plVar4 = *(longlong **)param_2;
      iVar1 = (int)*plVar4 + 1;
      if (iVar1 != 0) {
        *(int *)plVar4 = iVar1;
      }
      goto LAB_1800076fb;
    }
LAB_180007666:
    param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                 "%.200s() takes %.8s %zd positional argument%.1s (%zd given)","is_pyc_encrypted",
                 "exactly",1,&DAT_180010bad,param_3);
    plVar4 = (longlong *)0x0;
  }
  else {
    lVar2 = *(longlong *)(param_4 + 0x10);
    plVar4 = (longlong *)0x0;
    if (lVar2 < 0) goto LAB_1800076a5;
    if (lVar2 < 1) goto LAB_18000765c;
    if (param_3 != 0) {
      if (param_3 != 1) goto LAB_180007666;
      local_res10 = *(longlong **)param_2;
      iVar1 = (int)*local_res10 + 1;
      if (iVar1 != 0) {
        *(int *)local_res10 = iVar1;
      }
    }
    param_2 = param_2 + param_3 * 8;
    lVar2 = FUN_18000ac00(param_4,(undefined8 *)param_2,(longlong *)&local_18,param_4,
                          (longlong)&local_res10,param_3,lVar2,"is_pyc_encrypted");
    plVar4 = local_res10;
    if (-1 < (int)lVar2) {
      for (; param_1 = param_4, param_3 < 1; param_3 = param_3 + 1) {
        if ((&local_res10)[param_3] == (longlong *)0x0) {
          param_2 = "%.200s() takes %.8s %zd positional argument%.1s (%zd given)";
          PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                       "%.200s() takes %.8s %zd positional argument%.1s (%zd given)",
                       "is_pyc_encrypted","exactly",1,&DAT_180010bad,param_3);
          plVar4 = local_res10;
          goto LAB_1800076a5;
        }
      }
LAB_1800076fb:
      puVar3 = FUN_180007740(param_1,(undefined *)plVar4);
      if (((plVar4 != (longlong *)0x0) && (-1 < (int)*plVar4)) &&
         (*plVar4 = *plVar4 + -1, *plVar4 == 0)) {
        _Py_Dealloc(plVar4);
      }
      return puVar3;
    }
  }
LAB_1800076a5:
  puVar3 = PTR_s__security_crypto_py_180011d38;
  if (((plVar4 != (longlong *)0x0) && (-1 < (int)*plVar4)) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)
     ) {
    _Py_Dealloc(plVar4);
  }
  FUN_18000d220("_security_crypto.is_pyc_encrypted",param_2,0x7f,puVar3);
  return (undefined *)0x0;
}



// ==== FUN_180007740 @ 180007740 ====

/* WARNING: Removing unreachable block (ram,0x000180007861) */
/* WARNING: Removing unreachable block (ram,0x000180007866) */
/* WARNING: Removing unreachable block (ram,0x00018000786c) */

undefined * FUN_180007740(undefined8 param_1,undefined *param_2)

{
  int iVar1;
  code *pcVar2;
  uint uVar3;
  longlong lVar4;
  longlong *plVar5;
  longlong *plVar6;
  longlong *plVar7;
  int iVar8;
  char *pcVar9;
  undefined *puVar10;
  
  pcVar9 = (char *)(ulonglong)((code *)param_2 == _Py_TrueStruct_exref);
  if (((code *)param_2 != _Py_NoneStruct_exref && (code *)param_2 != _Py_FalseStruct_exref) &&
      (code *)param_2 != _Py_TrueStruct_exref) {
    uVar3 = PyObject_IsTrue(param_2);
    pcVar9 = (char *)(ulonglong)uVar3;
  }
  puVar10 = PTR_s__security_crypto_py_180011d38;
  if (-1 < (int)pcVar9) {
    if ((int)pcVar9 == 0) {
      if (*(int *)param_2 + 1 == 0) {
        return param_2;
      }
      *(int *)param_2 = *(int *)param_2 + 1;
      return param_2;
    }
    lVar4 = PyObject_Size(param_2);
    pcVar2 = _Py_FalseStruct_exref;
    puVar10 = PTR_s__security_crypto_py_180011d38;
    if (lVar4 != -1) {
      if (lVar4 < 4) {
        if (*(int *)_Py_FalseStruct_exref + 1 == 0) {
          return _Py_FalseStruct_exref;
        }
        *(int *)_Py_FalseStruct_exref = *(int *)_Py_FalseStruct_exref + 1;
        return pcVar2;
      }
      lVar4 = *(longlong *)(*(longlong *)(param_2 + 8) + 0x70);
      if ((lVar4 == 0) || (pcVar2 = *(code **)(lVar4 + 8), pcVar2 == (code *)0x0)) {
        pcVar9 = "\'%.200s\' object is unsliceable";
        PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"\'%.200s\' object is unsliceable",
                     *(undefined8 *)(*(longlong *)(param_2 + 8) + 0x18));
        puVar10 = PTR_s__security_crypto_py_180011d38;
      }
      else {
        pcVar9 = (char *)DAT_180016830;
        plVar5 = (longlong *)(*pcVar2)(param_2);
        puVar10 = PTR_s__security_crypto_py_180011d38;
        if (plVar5 != (longlong *)0x0) {
          plVar6 = (longlong *)FUN_18000a140(DAT_180016928);
          if ((plVar6 != (longlong *)0x0) &&
             (pcVar9 = (char *)plVar6, plVar7 = (longlong *)PyObject_RichCompare(plVar5,plVar6,2),
             plVar7 != (longlong *)0x0)) {
            if ((-1 < (int)*plVar5) && (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
              _Py_Dealloc(plVar5);
            }
            if ((-1 < (int)*plVar6) && (*plVar6 = *plVar6 + -1, *plVar6 == 0)) {
              _Py_Dealloc(plVar6);
            }
            iVar1 = (int)*plVar7 + 1;
            iVar8 = (int)*plVar7;
            if (iVar1 != 0) {
              *(int *)plVar7 = iVar1;
              iVar8 = iVar1;
            }
            if (iVar8 < 0) {
              return (undefined *)plVar7;
            }
            *plVar7 = *plVar7 + -1;
            if (*plVar7 != 0) {
              return (undefined *)plVar7;
            }
            _Py_Dealloc(plVar7);
            return (undefined *)plVar7;
          }
          puVar10 = PTR_s__security_crypto_py_180011d38;
          if ((-1 < (int)*plVar5) && (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
            _Py_Dealloc(plVar5);
          }
          if (((plVar6 != (longlong *)0x0) && (-1 < (int)*plVar6)) &&
             (*plVar6 = *plVar6 + -1, *plVar6 == 0)) {
            _Py_Dealloc(plVar6);
          }
        }
      }
    }
  }
  FUN_18000d220("_security_crypto.is_pyc_encrypted",pcVar9,0x81,puVar10);
  return (undefined *)0x0;
}



// ==== FUN_180007940 @ 180007940 ====

undefined8 * FUN_180007940(longlong param_1)

{
  undefined8 *puVar1;
  
  if (DAT_180016ca8 < 1 || *(longlong *)(param_1 + 0x20) != 0x20) {
    puVar1 = (undefined8 *)(**(code **)(param_1 + 0x130))(param_1,0);
    if (puVar1 == (undefined8 *)0x0) {
      return (undefined8 *)0x0;
    }
  }
  else {
    DAT_180016ca8 = DAT_180016ca8 + -1;
    puVar1 = *(undefined8 **)(&DAT_180016c68 + (longlong)DAT_180016ca8 * 8);
    *puVar1 = 0;
    puVar1[1] = 0;
    puVar1[2] = 0;
    puVar1[3] = 0;
    PyObject_Init(puVar1,param_1);
    PyObject_GC_Track(puVar1);
  }
  return puVar1;
}



// ==== FUN_1800079c0 @ 1800079c0 ====

void FUN_1800079c0(longlong param_1)

{
  longlong *plVar1;
  int iVar2;
  
  if (*(longlong *)(*(longlong *)(param_1 + 8) + 0x188) != 0) {
    iVar2 = PyObject_GC_IsFinalized();
    if ((iVar2 == 0) && (*(code **)(*(longlong *)(param_1 + 8) + 0x30) == FUN_1800079c0)) {
      iVar2 = PyObject_CallFinalizerFromDealloc(param_1);
      if (iVar2 != 0) {
        return;
      }
    }
  }
  PyObject_GC_UnTrack(param_1);
  plVar1 = *(longlong **)(param_1 + 0x10);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x10) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  if (DAT_180016ca8 < 8 && *(longlong *)(*(longlong *)(param_1 + 8) + 0x20) == 0x20) {
    *(longlong *)(&DAT_180016c68 + (longlong)DAT_180016ca8 * 8) = param_1;
    DAT_180016ca8 = DAT_180016ca8 + 1;
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x000180007a77. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(*(longlong *)(param_1 + 8) + 0x140))(param_1);
  return;
}



// ==== FUN_180007aa0 @ 180007aa0 ====

undefined8 FUN_180007aa0(longlong param_1)

{
  longlong *plVar1;
  
  plVar1 = *(longlong **)(param_1 + 0x10);
  *(code **)(param_1 + 0x10) = _Py_NoneStruct_exref;
  if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
    *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
  }
  if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) && (*plVar1 = *plVar1 + -1, *plVar1 == 0)
     ) {
    _Py_Dealloc(plVar1);
  }
  return 0;
}



// ==== FUN_180007af0 @ 180007af0 ====

undefined8 * FUN_180007af0(longlong param_1)

{
  undefined8 *puVar1;
  
  if (DAT_180016cf0 < 1 || *(longlong *)(param_1 + 0x20) != 0x50) {
    puVar1 = (undefined8 *)(**(code **)(param_1 + 0x130))(param_1,0);
    if (puVar1 == (undefined8 *)0x0) {
      return (undefined8 *)0x0;
    }
  }
  else {
    DAT_180016cf0 = DAT_180016cf0 + -1;
    puVar1 = *(undefined8 **)(&DAT_180016cb0 + (longlong)DAT_180016cf0 * 8);
    *puVar1 = 0;
    puVar1[1] = 0;
    puVar1[2] = 0;
    puVar1[3] = 0;
    puVar1[4] = 0;
    puVar1[5] = 0;
    puVar1[6] = 0;
    puVar1[7] = 0;
    puVar1[8] = 0;
    puVar1[9] = 0;
    PyObject_Init(puVar1,param_1);
    PyObject_GC_Track(puVar1);
  }
  return puVar1;
}



// ==== FUN_180007b80 @ 180007b80 ====

void FUN_180007b80(longlong param_1)

{
  longlong *plVar1;
  int iVar2;
  
  if (*(longlong *)(*(longlong *)(param_1 + 8) + 0x188) != 0) {
    iVar2 = PyObject_GC_IsFinalized();
    if ((iVar2 == 0) && (*(code **)(*(longlong *)(param_1 + 8) + 0x30) == FUN_180007b80)) {
      iVar2 = PyObject_CallFinalizerFromDealloc(param_1);
      if (iVar2 != 0) {
        return;
      }
    }
  }
  PyObject_GC_UnTrack(param_1);
  plVar1 = *(longlong **)(param_1 + 0x10);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x10) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x18);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x18) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x20);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x20) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x28);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x28) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x30);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x30) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x38);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x38) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  if (DAT_180016cf0 < 8 && *(longlong *)(*(longlong *)(param_1 + 8) + 0x20) == 0x50) {
    *(longlong *)(&DAT_180016cb0 + (longlong)DAT_180016cf0 * 8) = param_1;
    DAT_180016cf0 = DAT_180016cf0 + 1;
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x000180007ccc. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(*(longlong *)(param_1 + 8) + 0x140))(param_1);
  return;
}



// ==== FUN_180007ce0 @ 180007ce0 ====

undefined8 FUN_180007ce0(longlong param_1,undefined *UNRECOVERED_JUMPTABLE,undefined8 param_3)

{
  undefined8 uVar1;
  
  if ((*(longlong *)(param_1 + 0x10) != 0) &&
     (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x10),param_3),
     (int)uVar1 != 0)) {
    return uVar1;
  }
  if ((*(longlong *)(param_1 + 0x18) != 0) &&
     (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x18),param_3),
     (int)uVar1 != 0)) {
    return uVar1;
  }
  if ((*(longlong *)(param_1 + 0x20) != 0) &&
     (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x20),param_3),
     (int)uVar1 != 0)) {
    return uVar1;
  }
  if ((*(longlong *)(param_1 + 0x28) != 0) &&
     (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x28),param_3),
     (int)uVar1 != 0)) {
    return uVar1;
  }
  if ((*(longlong *)(param_1 + 0x30) != 0) &&
     (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x30),param_3),
     (int)uVar1 != 0)) {
    return uVar1;
  }
  if (*(longlong *)(param_1 + 0x38) == 0) {
    return 0;
  }
                    /* WARNING: Could not recover jumptable at 0x000180007d70. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x38),param_3);
  return uVar1;
}



// ==== FUN_180007d90 @ 180007d90 ====

undefined8 * FUN_180007d90(longlong param_1)

{
  undefined8 *puVar1;
  
  if (DAT_180016d38 < 1 || *(longlong *)(param_1 + 0x20) != 0x20) {
    puVar1 = (undefined8 *)(**(code **)(param_1 + 0x130))(param_1,0);
    if (puVar1 == (undefined8 *)0x0) {
      return (undefined8 *)0x0;
    }
  }
  else {
    DAT_180016d38 = DAT_180016d38 + -1;
    puVar1 = *(undefined8 **)(&DAT_180016cf8 + (longlong)DAT_180016d38 * 8);
    *puVar1 = 0;
    puVar1[1] = 0;
    puVar1[2] = 0;
    puVar1[3] = 0;
    PyObject_Init(puVar1,param_1);
    PyObject_GC_Track(puVar1);
  }
  return puVar1;
}



// ==== FUN_180007e10 @ 180007e10 ====

void FUN_180007e10(longlong param_1)

{
  longlong *plVar1;
  int iVar2;
  
  if (*(longlong *)(*(longlong *)(param_1 + 8) + 0x188) != 0) {
    iVar2 = PyObject_GC_IsFinalized();
    if ((iVar2 == 0) && (*(code **)(*(longlong *)(param_1 + 8) + 0x30) == FUN_180007e10)) {
      iVar2 = PyObject_CallFinalizerFromDealloc(param_1);
      if (iVar2 != 0) {
        return;
      }
    }
  }
  PyObject_GC_UnTrack(param_1);
  plVar1 = *(longlong **)(param_1 + 0x10);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x10) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  if (DAT_180016d38 < 8 && *(longlong *)(*(longlong *)(param_1 + 8) + 0x20) == 0x20) {
    *(longlong *)(&DAT_180016cf8 + (longlong)DAT_180016d38 * 8) = param_1;
    DAT_180016d38 = DAT_180016d38 + 1;
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x000180007ec7. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(*(longlong *)(param_1 + 8) + 0x140))(param_1);
  return;
}



// ==== FUN_180007ed0 @ 180007ed0 ====

undefined8 * FUN_180007ed0(longlong param_1)

{
  undefined8 *puVar1;
  
  if (DAT_180016d80 < 1 || *(longlong *)(param_1 + 0x20) != 0x50) {
    puVar1 = (undefined8 *)(**(code **)(param_1 + 0x130))(param_1,0);
    if (puVar1 == (undefined8 *)0x0) {
      return (undefined8 *)0x0;
    }
  }
  else {
    DAT_180016d80 = DAT_180016d80 + -1;
    puVar1 = *(undefined8 **)(&DAT_180016d40 + (longlong)DAT_180016d80 * 8);
    *puVar1 = 0;
    puVar1[1] = 0;
    puVar1[2] = 0;
    puVar1[3] = 0;
    puVar1[4] = 0;
    puVar1[5] = 0;
    puVar1[6] = 0;
    puVar1[7] = 0;
    puVar1[8] = 0;
    puVar1[9] = 0;
    PyObject_Init(puVar1,param_1);
    PyObject_GC_Track(puVar1);
  }
  return puVar1;
}



// ==== FUN_180007f60 @ 180007f60 ====

void FUN_180007f60(longlong param_1)

{
  longlong *plVar1;
  int iVar2;
  
  if (*(longlong *)(*(longlong *)(param_1 + 8) + 0x188) != 0) {
    iVar2 = PyObject_GC_IsFinalized();
    if ((iVar2 == 0) && (*(code **)(*(longlong *)(param_1 + 8) + 0x30) == FUN_180007f60)) {
      iVar2 = PyObject_CallFinalizerFromDealloc(param_1);
      if (iVar2 != 0) {
        return;
      }
    }
  }
  PyObject_GC_UnTrack(param_1);
  plVar1 = *(longlong **)(param_1 + 0x10);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x10) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x18);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x18) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x20);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x20) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x28);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x28) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x30);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x30) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x38);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x38) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  if (DAT_180016d80 < 8 && *(longlong *)(*(longlong *)(param_1 + 8) + 0x20) == 0x50) {
    *(longlong *)(&DAT_180016d40 + (longlong)DAT_180016d80 * 8) = param_1;
    DAT_180016d80 = DAT_180016d80 + 1;
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x0001800080ac. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(*(longlong *)(param_1 + 8) + 0x140))(param_1);
  return;
}



// ==== PyInit__security_crypto @ 1800080c0 ====

void PyInit__security_crypto(void)

{
                    /* 0x80c0  1  PyInit__security_crypto */
                    /* WARNING: Could not recover jumptable at 0x0001800080c7. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  PyModuleDef_Init(&DAT_180015cd0);
  return;
}



// ==== FUN_1800080d0 @ 1800080d0 ====

longlong * FUN_1800080d0(undefined8 param_1)

{
  longlong lVar1;
  longlong lVar2;
  longlong *plVar3;
  longlong *plVar4;
  code *pcVar5;
  int iVar6;
  
  lVar2 = PyThreadState_Get();
  lVar2 = PyInterpreterState_GetID(*(undefined8 *)(lVar2 + 0x10));
  if (lVar2 == -1) {
    return (longlong *)0x0;
  }
  lVar1 = lVar2;
  if ((DAT_180015a60 != -1) && (lVar1 = DAT_180015a60, DAT_180015a60 != lVar2)) {
    PyErr_SetString(*(undefined8 *)PyExc_ImportError_exref,
                    "Interpreter change detected - this module can only be loaded into one interpreter per process."
                   );
    return (longlong *)0x0;
  }
  DAT_180015a60 = lVar1;
  plVar3 = DAT_180016de0;
  if (DAT_180016de0 != (longlong *)0x0) {
    iVar6 = (int)*DAT_180016de0 + 1;
    if (iVar6 != 0) {
      *(int *)DAT_180016de0 = iVar6;
      return plVar3;
    }
    return DAT_180016de0;
  }
  plVar3 = (longlong *)PyObject_GetAttrString(param_1,&DAT_180010aa0);
  if (plVar3 == (longlong *)0x0) {
    return (longlong *)0x0;
  }
  plVar4 = (longlong *)PyModule_NewObject(plVar3);
  if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
    _Py_Dealloc(plVar3);
  }
  if (plVar4 == (longlong *)0x0) {
    return (longlong *)0x0;
  }
  lVar2 = PyModule_GetDict(plVar4);
  if (lVar2 != 0) {
    plVar3 = (longlong *)PyObject_GetAttrString(param_1,"loader");
    if (plVar3 == (longlong *)0x0) {
      iVar6 = PyErr_ExceptionMatches(*(undefined8 *)PyExc_AttributeError_exref);
      if (iVar6 == 0) goto LAB_1800081f3;
      PyErr_Clear();
    }
    else {
      iVar6 = PyDict_SetItemString(lVar2,"__loader__",plVar3);
      if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
        _Py_Dealloc(plVar3);
      }
      if (iVar6 < 0) goto LAB_1800081f3;
    }
    plVar3 = (longlong *)PyObject_GetAttrString(param_1,"origin");
    if (plVar3 == (longlong *)0x0) {
      iVar6 = PyErr_ExceptionMatches(*(undefined8 *)PyExc_AttributeError_exref);
      if (iVar6 == 0) goto LAB_1800081f3;
      PyErr_Clear();
    }
    else {
      iVar6 = PyDict_SetItemString(lVar2,"__file__",plVar3);
      if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
        _Py_Dealloc(plVar3);
      }
      if (iVar6 < 0) goto LAB_1800081f3;
    }
    plVar3 = (longlong *)PyObject_GetAttrString(param_1,"parent");
    if (plVar3 == (longlong *)0x0) {
      iVar6 = PyErr_ExceptionMatches(*(undefined8 *)PyExc_AttributeError_exref);
      if (iVar6 == 0) goto LAB_1800081f3;
      PyErr_Clear();
    }
    else {
      iVar6 = PyDict_SetItemString(lVar2,"__package__",plVar3);
      if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
        _Py_Dealloc(plVar3);
      }
      if (iVar6 < 0) goto LAB_1800081f3;
    }
    pcVar5 = (code *)PyObject_GetAttrString(param_1,"submodule_search_locations");
    iVar6 = 0;
    if (pcVar5 == (code *)0x0) {
      iVar6 = PyErr_ExceptionMatches(*(undefined8 *)PyExc_AttributeError_exref);
      if (iVar6 != 0) {
        PyErr_Clear();
        return plVar4;
      }
    }
    else {
      if (pcVar5 != _Py_NoneStruct_exref) {
        iVar6 = PyDict_SetItemString(lVar2,"__path__",pcVar5);
      }
      if ((-1 < *(int *)pcVar5) &&
         (*(longlong *)pcVar5 = *(longlong *)pcVar5 + -1, *(longlong *)pcVar5 == 0)) {
        _Py_Dealloc(pcVar5);
      }
      if (-1 < iVar6) {
        return plVar4;
      }
    }
  }
LAB_1800081f3:
  if ((-1 < (int)*plVar4) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)) {
    _Py_Dealloc(plVar4);
  }
  return (longlong *)0x0;
}



// ==== FUN_180008390 @ 180008390 ====

/* WARNING: Function: __security_check_cookie replaced with injection: security_check_cookie */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_180008390(longlong *param_1,char *param_2)

{
  bool bVar1;
  bool bVar2;
  longlong **pplVar3;
  int iVar4;
  int iVar5;
  undefined8 uVar6;
  longlong *plVar7;
  longlong lVar8;
  longlong lVar9;
  ulonglong uVar10;
  longlong *plVar11;
  longlong *plVar12;
  undefined *puVar13;
  undefined1 auStackY_178 [32];
  longlong local_128 [2];
  longlong *local_118 [2];
  longlong *local_108 [26];
  ulonglong local_38;
  
  local_38 = DAT_180015000 ^ (ulonglong)auStackY_178;
  bVar1 = false;
  bVar2 = false;
  if (DAT_180016de0 != (longlong *)0x0) {
    if (DAT_180016de0 == param_1) {
      return 0;
    }
    PyErr_SetString(*(undefined8 *)PyExc_RuntimeError_exref,
                    "Module \'_security_crypto\' has already been imported. Re-initialisation is not supported."
                   );
    return -1;
  }
  iVar4 = (int)*param_1 + 1;
  if (iVar4 != 0) {
    *(int *)param_1 = iVar4;
  }
  DAT_180016de0 = param_1;
  DAT_180016730 = (int *)PyModule_GetDict();
  if (DAT_180016730 == (int *)0x0) {
LAB_180009309:
    iVar4 = 1;
    puVar13 = PTR_s__security_crypto_py_180011d38;
    bVar1 = bVar2;
  }
  else {
    if (*DAT_180016730 + 1 != 0) {
      *DAT_180016730 = *DAT_180016730 + 1;
    }
    DAT_180016738 = PyImport_AddModuleRef("builtins");
    if ((DAT_180016738 == 0) ||
       (_DAT_180016740 = PyImport_AddModuleRef("cython_runtime"), _DAT_180016740 == 0))
    goto LAB_180009309;
    param_2 = "__builtins__";
    iVar5 = PyObject_SetAttrString(DAT_180016de0,"__builtins__",DAT_180016738);
    iVar4 = 1;
    puVar13 = PTR_s__security_crypto_py_180011d38;
    if (-1 < iVar5) {
      param_2 = (char *)(ulonglong)*(uint *)Py_Version_exref;
      if ((*(uint *)Py_Version_exref & 0xffff0000) != 0x30d0000) {
        PyOS_snprintf(local_108,200,
                      "compile time Python version %d.%d of module \'%.100s\' %s runtime version %d.%d"
                     );
        param_2 = (char *)local_108;
        iVar5 = PyErr_WarnEx(0,param_2,1);
        puVar13 = PTR_s__security_crypto_py_180011d38;
        if (iVar5 < 0) goto LAB_180009315;
      }
      DAT_180016748 = PyTuple_New(0);
      puVar13 = PTR_s__security_crypto_py_180011d38;
      if (DAT_180016748 != 0) {
        param_2 = (char *)0x0;
        DAT_180016750 = PyBytes_FromStringAndSize(&DAT_180010bad);
        puVar13 = PTR_s__security_crypto_py_180011d38;
        bVar1 = bVar2;
        if (DAT_180016750 != 0) {
          param_2 = (char *)0x0;
          DAT_180016758 = PyUnicode_FromStringAndSize(&DAT_180010bad);
          puVar13 = PTR_s__security_crypto_py_180011d38;
          if ((DAT_180016758 != 0) &&
             (uVar6 = FUN_1800093f0(0x180016730), puVar13 = PTR_s__security_crypto_py_180011d38,
             -1 < (int)uVar6)) {
            bVar2 = true;
            param_2 = (char *)PyType_Type_exref;
            plVar7 = (longlong *)PyTuple_Pack();
            bVar1 = bVar2;
            if (plVar7 == (longlong *)0x0) {
LAB_1800085e7:
              lVar8 = PyErr_Occurred();
              puVar13 = PTR_s__security_crypto_py_180011d38;
              if (lVar8 != 0) goto LAB_180009315;
            }
            else {
              DAT_180016d88 =
                   FUN_18000ba20(0,param_2,&PTR_s__cython_3_2_4__common_types_meta_1800158a0,plVar7)
              ;
              if ((-1 < (int)*plVar7) && (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                _Py_Dealloc(plVar7);
              }
              if (DAT_180016d88 == (longlong *)0x0) goto LAB_1800085e7;
            }
            lVar8 = PyErr_Occurred();
            puVar13 = PTR_s__security_crypto_py_180011d38;
            if ((((lVar8 == 0) &&
                 ((DAT_180016d90 =
                        FUN_18000ba20(DAT_180016d88,param_2,
                                      &PTR_s__cython_3_2_4_cython_function_or_180016080,0),
                  DAT_180016d90 != (longlong *)0x0 ||
                  (lVar8 = PyErr_Occurred(), puVar13 = PTR_s__security_crypto_py_180011d38,
                  lVar8 == 0)))) &&
                ((DAT_180016da8 =
                       FUN_18000ba20(DAT_180016d88,param_2,&PTR_s__cython_3_2_4_generator_180016100,
                                     0), DAT_180016da8 != (longlong *)0x0 ||
                 (lVar8 = PyErr_Occurred(), puVar13 = PTR_s__security_crypto_py_180011d38,
                 lVar8 == 0)))) &&
               (((DAT_180016db4 == 0 ||
                 (param_2 = (char *)DAT_180016a98,
                 iVar5 = PyObject_SetAttr(DAT_180016de0,DAT_180016a98,DAT_180016a88),
                 puVar13 = PTR_s__security_crypto_py_180011d38, -1 < iVar5)) &&
                (lVar8 = PyImport_GetModuleDict(), puVar13 = PTR_s__security_crypto_py_180011d38,
                lVar8 != 0)))) {
              lVar9 = PyDict_GetItemString(lVar8,"_security_crypto");
              if (lVar9 == 0) {
                param_2 = "_security_crypto";
                iVar5 = PyDict_SetItemString(lVar8,"_security_crypto",DAT_180016de0);
                puVar13 = PTR_s__security_crypto_py_180011d38;
                if (iVar5 < 0) goto LAB_180009315;
              }
              pplVar3 = DAT_1800169e0;
              param_2 = (char *)DAT_1800169e0;
              PyObject_GetOptionalAttr(DAT_180016738,DAT_1800169e0,local_128);
              if ((local_128[0] == 0) && (lVar8 = PyErr_Occurred(), lVar8 == 0)) {
                param_2 = "name \'%U\' is not defined";
                PyErr_Format(*(undefined8 *)PyExc_NameError_exref,"name \'%U\' is not defined",
                             pplVar3);
              }
              _DAT_180016dd8 = local_128[0];
              puVar13 = PTR_s__security_crypto_py_180011d38;
              if (local_128[0] != 0) {
                _DAT_1800167a8 = &DAT_180016a38;
                _DAT_1800167d0 = &DAT_180016ad8;
                _DAT_1800167a0 = PyDict_Type_exref;
                _DAT_1800167c8 = PyDict_Type_exref;
                _DAT_1800167f0 = PyDict_Type_exref;
                _DAT_1800167f8 = &DAT_180016b70;
                param_2 = (char *)DAT_180016c30;
                DAT_180016818 = PySlice_New(_Py_NoneStruct_exref,DAT_180016c30,_Py_NoneStruct_exref)
                ;
                puVar13 = PTR_s__security_crypto_py_180011d38;
                if ((((DAT_180016818 != 0) &&
                     (param_2 = (char *)_Py_NoneStruct_exref,
                     DAT_180016820 =
                          PySlice_New(DAT_180016c30,_Py_NoneStruct_exref,_Py_NoneStruct_exref),
                     puVar13 = PTR_s__security_crypto_py_180011d38, DAT_180016820 != 0)) &&
                    ((param_2 = (char *)DAT_180016c38,
                     DAT_180016850 = PyTuple_Pack(2,DAT_180016c38,DAT_180016a60),
                     puVar13 = PTR_s__security_crypto_py_180011d38, DAT_180016850 != 0 &&
                     ((((param_2 = (char *)DAT_180016c50,
                        DAT_180016828 =
                             PySlice_New(_Py_NoneStruct_exref,DAT_180016c50,_Py_NoneStruct_exref),
                        puVar13 = PTR_s__security_crypto_py_180011d38, DAT_180016828 != 0 &&
                        (param_2 = (char *)DAT_180016c38,
                        DAT_180016830 =
                             PySlice_New(_Py_NoneStruct_exref,DAT_180016c38,_Py_NoneStruct_exref),
                        puVar13 = PTR_s__security_crypto_py_180011d38, DAT_180016830 != 0)) &&
                       (param_2 = (char *)DAT_180016c58,
                       DAT_180016838 = PySlice_New(DAT_180016c38,DAT_180016c58,_Py_NoneStruct_exref)
                       , puVar13 = PTR_s__security_crypto_py_180011d38, DAT_180016838 != 0)) &&
                      ((param_2 = (char *)_Py_NoneStruct_exref,
                       DAT_180016840 =
                            PySlice_New(DAT_180016c48,_Py_NoneStruct_exref,_Py_NoneStruct_exref),
                       puVar13 = PTR_s__security_crypto_py_180011d38, DAT_180016840 != 0 &&
                       (param_2 = (char *)DAT_180016c48,
                       DAT_180016848 = PySlice_New(DAT_180016c58,DAT_180016c48,_Py_NoneStruct_exref)
                       , puVar13 = PTR_s__security_crypto_py_180011d38, DAT_180016848 != 0))))))))
                   && (uVar6 = FUN_180009a20(0x180016730),
                      puVar13 = PTR_s__security_crypto_py_180011d38, -1 < (int)uVar6)) {
                  DAT_180016780 = &DAT_180015d40;
                  uVar10 = FUN_18000b890(0x180015d40);
                  puVar13 = PTR_s__security_crypto_py_180011d38;
                  if (-1 < (int)uVar10) {
                    if ((*(longlong *)(DAT_180016780 + 0x120) == 0) &&
                       (*(code **)(DAT_180016780 + 0x90) == PyObject_GenericGetAttr_exref)) {
                      *(code **)(DAT_180016780 + 0x90) = PyObject_GenericGetAttr_exref;
                    }
                    DAT_180016788 = &DAT_1800158c0;
                    uVar10 = FUN_18000b890(0x1800158c0);
                    puVar13 = PTR_s__security_crypto_py_180011d38;
                    if (-1 < (int)uVar10) {
                      if ((*(longlong *)(DAT_180016788 + 0x120) == 0) &&
                         (*(code **)(DAT_180016788 + 0x90) == PyObject_GenericGetAttr_exref)) {
                        *(code **)(DAT_180016788 + 0x90) = PyObject_GenericGetAttr_exref;
                      }
                      DAT_180016790 = &DAT_180015af0;
                      uVar10 = FUN_18000b890(0x180015af0);
                      puVar13 = PTR_s__security_crypto_py_180011d38;
                      if (-1 < (int)uVar10) {
                        if ((*(longlong *)(DAT_180016790 + 0x120) == 0) &&
                           (*(code **)(DAT_180016790 + 0x90) == PyObject_GenericGetAttr_exref)) {
                          *(code **)(DAT_180016790 + 0x90) = PyObject_GenericGetAttr_exref;
                        }
                        DAT_180016798 = &DAT_180015ee0;
                        uVar10 = FUN_18000b890(0x180015ee0);
                        puVar13 = PTR_s__security_crypto_py_180011d38;
                        if (-1 < (int)uVar10) {
                          if ((*(longlong *)(DAT_180016798 + 0x120) == 0) &&
                             (*(code **)(DAT_180016798 + 0x90) == PyObject_GenericGetAttr_exref)) {
                            *(code **)(DAT_180016798 + 0x90) = PyObject_GenericGetAttr_exref;
                          }
                          plVar7 = FUN_18000b560(DAT_180016a08);
                          if (plVar7 == (longlong *)0x0) {
                            iVar4 = 2;
                            puVar13 = PTR_s__security_crypto_py_180011d38;
                          }
                          else {
                            param_2 = (char *)DAT_180016a08;
                            iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016a08,plVar7);
                            if (iVar5 < 0) {
                              iVar4 = 2;
LAB_1800092d4:
                              puVar13 = PTR_s__security_crypto_py_180011d38;
                              bVar1 = true;
                              if ((-1 < (int)*plVar7) &&
                                 (*plVar7 = *plVar7 + -1, bVar1 = bVar2, *plVar7 == 0)) {
                                _Py_Dealloc(plVar7);
                              }
                            }
                            else {
                              if ((-1 < (int)*plVar7) && (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                _Py_Dealloc(plVar7);
                              }
                              plVar7 = FUN_18000b560(DAT_180016ad0);
                              if (plVar7 == (longlong *)0x0) {
                                iVar4 = 3;
                                puVar13 = PTR_s__security_crypto_py_180011d38;
                              }
                              else {
                                param_2 = (char *)DAT_180016ad0;
                                iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016ad0,plVar7);
                                if (iVar5 < 0) {
                                  iVar4 = 3;
                                  goto LAB_1800092d4;
                                }
                                if ((-1 < (int)*plVar7) && (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                  _Py_Dealloc(plVar7);
                                }
                                plVar7 = FUN_18000b560(DAT_180016b60);
                                if (plVar7 == (longlong *)0x0) {
                                  iVar4 = 4;
                                  puVar13 = PTR_s__security_crypto_py_180011d38;
                                }
                                else {
                                  param_2 = (char *)DAT_180016b60;
                                  iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016b60,plVar7);
                                  if (iVar5 < 0) {
                                    iVar4 = 4;
                                    goto LAB_1800092d4;
                                  }
                                  if ((-1 < (int)*plVar7) && (*plVar7 = *plVar7 + -1, *plVar7 == 0))
                                  {
                                    _Py_Dealloc(plVar7);
                                  }
                                  plVar7 = FUN_18000b560(DAT_180016b80);
                                  if (plVar7 == (longlong *)0x0) {
                                    iVar4 = 5;
                                    puVar13 = PTR_s__security_crypto_py_180011d38;
                                  }
                                  else {
                                    param_2 = (char *)DAT_180016b80;
                                    iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016b80,plVar7);
                                    if (iVar5 < 0) {
                                      iVar4 = 5;
                                      goto LAB_1800092d4;
                                    }
                                    if ((-1 < (int)*plVar7) &&
                                       (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                      _Py_Dealloc(plVar7);
                                    }
                                    plVar7 = FUN_18000b560(DAT_180016a70);
                                    if (plVar7 == (longlong *)0x0) {
                                      iVar4 = 6;
                                      puVar13 = PTR_s__security_crypto_py_180011d38;
                                    }
                                    else {
                                      param_2 = (char *)DAT_180016a70;
                                      iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016a70,plVar7);
                                      if (iVar5 < 0) {
                                        iVar4 = 6;
                                        goto LAB_1800092d4;
                                      }
                                      if ((-1 < (int)*plVar7) &&
                                         (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                        _Py_Dealloc(plVar7);
                                      }
                                      plVar7 = (longlong *)FUN_18000a140((longlong)DAT_180016a70);
                                      if (plVar7 == (longlong *)0x0) {
                                        iVar4 = 8;
                                        puVar13 = PTR_s__security_crypto_py_180011d38;
                                      }
                                      else {
                                        param_2 = (char *)DAT_1800169f8;
                                        if (*(code **)(plVar7[1] + 0x90) == (code *)0x0) {
                                          plVar11 = (longlong *)PyObject_GetAttr(plVar7);
                                        }
                                        else {
                                          plVar11 = (longlong *)(**(code **)(plVar7[1] + 0x90))();
                                        }
                                        if (plVar11 == (longlong *)0x0) {
                                          iVar4 = 8;
                                          goto LAB_1800092d4;
                                        }
                                        if ((-1 < (int)*plVar7) &&
                                           (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                          _Py_Dealloc(plVar7);
                                        }
                                        plVar12 = (longlong *)FUN_18000a140((longlong)DAT_180016a98)
                                        ;
                                        puVar13 = PTR_s__security_crypto_py_180011d38;
                                        if (plVar12 == (longlong *)0x0) {
                                          iVar4 = 8;
                                          if ((-1 < (int)*plVar11) &&
                                             (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
                                            _Py_Dealloc(plVar11);
                                          }
                                        }
                                        else {
                                          uVar6 = 0;
                                          local_128[1] = 0;
                                          param_2 = (char *)local_118;
                                          local_118[0] = plVar12;
                                          plVar7 = (longlong *)
                                                   FUN_18000a310((longlong)plVar11,
                                                                 (undefined8 *)param_2,
                                                                 0x8000000000000001,0);
                                          if ((-1 < (int)*plVar12) &&
                                             (*plVar12 = *plVar12 + -1, *plVar12 == 0)) {
                                            _Py_Dealloc(plVar12);
                                          }
                                          if ((-1 < (int)*plVar11) &&
                                             (*plVar11 = *plVar11 + -1, *plVar11 == 0)) {
                                            _Py_Dealloc(plVar11);
                                          }
                                          if (plVar7 == (longlong *)0x0) {
                                            iVar4 = 8;
                                            puVar13 = PTR_s__security_crypto_py_180011d38;
                                          }
                                          else {
                                            param_2 = (char *)DAT_180016a68;
                                            iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016a68,
                                                                   plVar7);
                                            if (iVar5 < 0) {
                                              iVar4 = 8;
                                              goto LAB_1800092d4;
                                            }
                                            if ((-1 < (int)*plVar7) &&
                                               (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                              _Py_Dealloc(plVar7);
                                            }
                                            param_2 = (char *)DAT_180016908;
                                            iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016908,
                                                                   DAT_180016b98);
                                            if (iVar5 < 0) {
                                              iVar4 = 10;
                                              puVar13 = PTR_s__security_crypto_py_180011d38;
                                            }
                                            else {
                                              param_2 = (char *)DAT_180016910;
                                              iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016910,
                                                                     DAT_180016c10);
                                              if (iVar5 < 0) {
                                                iVar4 = 0xb;
                                                puVar13 = PTR_s__security_crypto_py_180011d38;
                                              }
                                              else {
                                                plVar7 = (longlong *)
                                                         FUN_18000ced0(0x180015aa8,param_2,
                                                                       (int *)DAT_180016a80,uVar6,
                                                                       DAT_180016b00,DAT_180016730,
                                                                       DAT_180016868);
                                                if (plVar7 == (longlong *)0x0) {
                                                  iVar4 = 0xe;
                                                  puVar13 = PTR_s__security_crypto_py_180011d38;
                                                }
                                                else {
                                                  param_2 = (char *)DAT_180016a80;
                                                  iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016a80
                                                                         ,plVar7);
                                                  if (iVar5 < 0) {
                                                    iVar4 = 0xe;
                                                    goto LAB_1800092d4;
                                                  }
                                                  if ((-1 < (int)*plVar7) &&
                                                     (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                                    _Py_Dealloc(plVar7);
                                                  }
                                                  plVar7 = (longlong *)
                                                           FUN_18000ced0(0x1800160c0,param_2,
                                                                         (int *)DAT_1800169c0,uVar6,
                                                                         DAT_180016b00,DAT_180016730
                                                                         ,DAT_180016870);
                                                  if (plVar7 == (longlong *)0x0) {
                                                    iVar4 = 0x1c;
                                                    puVar13 = PTR_s__security_crypto_py_180011d38;
                                                  }
                                                  else {
                                                    param_2 = (char *)DAT_1800169c0;
                                                    iVar5 = PyDict_SetItem(DAT_180016730,
                                                                           DAT_1800169c0,plVar7);
                                                    if (iVar5 < 0) {
                                                      iVar4 = 0x1c;
                                                      goto LAB_1800092d4;
                                                    }
                                                    if ((-1 < (int)*plVar7) &&
                                                       (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                                      _Py_Dealloc(plVar7);
                                                    }
                                                    plVar7 = (longlong *)
                                                             FUN_18000ced0(0x1800160a0,param_2,
                                                                           (int *)DAT_180016988,
                                                                           uVar6,DAT_180016b00,
                                                                           DAT_180016730,
                                                                           DAT_180016878);
                                                    if (plVar7 == (longlong *)0x0) {
                                                      iVar4 = 0x29;
                                                      puVar13 = PTR_s__security_crypto_py_180011d38;
                                                    }
                                                    else {
                                                      param_2 = (char *)DAT_180016988;
                                                      iVar5 = PyDict_SetItem(DAT_180016730,
                                                                             DAT_180016988,plVar7);
                                                      if (iVar5 < 0) {
                                                        iVar4 = 0x29;
                                                        goto LAB_1800092d4;
                                                      }
                                                      if ((-1 < (int)*plVar7) &&
                                                         (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                                        _Py_Dealloc(plVar7);
                                                      }
                                                      plVar7 = (longlong *)
                                                               FUN_18000ced0(0x180015880,param_2,
                                                                             (int *)DAT_180016998,
                                                                             uVar6,DAT_180016b00,
                                                                             DAT_180016730,
                                                                             DAT_180016880);
                                                      if (plVar7 == (longlong *)0x0) {
                                                        iVar4 = 0x35;
                                                        puVar13 = 
                                                  PTR_s__security_crypto_py_180011d38;
                                                  }
                                                  else {
                                                    param_2 = (char *)DAT_180016998;
                                                    iVar5 = PyDict_SetItem(DAT_180016730,
                                                                           DAT_180016998,plVar7);
                                                    if (iVar5 < 0) {
                                                      iVar4 = 0x35;
                                                      goto LAB_1800092d4;
                                                    }
                                                    if ((-1 < (int)*plVar7) &&
                                                       (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                                      _Py_Dealloc(plVar7);
                                                    }
                                                    plVar7 = (longlong *)
                                                             FUN_18000ced0(0x180015ac8,param_2,
                                                                           (int *)DAT_180016a28,
                                                                           uVar6,DAT_180016b00,
                                                                           DAT_180016730,
                                                                           DAT_180016888);
                                                    if (plVar7 == (longlong *)0x0) {
                                                      iVar4 = 0x40;
                                                      puVar13 = PTR_s__security_crypto_py_180011d38;
                                                    }
                                                    else {
                                                      param_2 = (char *)DAT_180016a28;
                                                      iVar5 = PyDict_SetItem(DAT_180016730,
                                                                             DAT_180016a28,plVar7);
                                                      if (iVar5 < 0) {
                                                        iVar4 = 0x40;
                                                        goto LAB_1800092d4;
                                                      }
                                                      if ((-1 < (int)*plVar7) &&
                                                         (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                                        _Py_Dealloc(plVar7);
                                                      }
                                                      plVar7 = (longlong *)
                                                               FUN_18000ced0(0x1800160e0,param_2,
                                                                             (int *)DAT_180016b78,
                                                                             uVar6,DAT_180016b00,
                                                                             DAT_180016730,
                                                                             DAT_180016890);
                                                      if (plVar7 == (longlong *)0x0) {
                                                        iVar4 = 0x46;
                                                        puVar13 = 
                                                  PTR_s__security_crypto_py_180011d38;
                                                  }
                                                  else {
                                                    param_2 = (char *)DAT_180016b78;
                                                    iVar5 = PyDict_SetItem(DAT_180016730,
                                                                           DAT_180016b78,plVar7);
                                                    if (iVar5 < 0) {
                                                      iVar4 = 0x46;
                                                      goto LAB_1800092d4;
                                                    }
                                                    if ((-1 < (int)*plVar7) &&
                                                       (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                                      _Py_Dealloc(plVar7);
                                                    }
                                                    param_2 = (char *)DAT_180016920;
                                                    iVar5 = PyDict_SetItem(DAT_180016730,
                                                                           DAT_180016920,
                                                                           DAT_180016c00);
                                                    if (iVar5 < 0) {
                                                      iVar4 = 0x51;
                                                      puVar13 = PTR_s__security_crypto_py_180011d38;
                                                    }
                                                    else {
                                                      param_2 = (char *)DAT_180016918;
                                                      iVar5 = PyDict_SetItem(DAT_180016730,
                                                                             DAT_180016918,
                                                                             DAT_180016b88);
                                                      if (iVar5 < 0) {
                                                        iVar4 = 0x52;
                                                        puVar13 = 
                                                  PTR_s__security_crypto_py_180011d38;
                                                  }
                                                  else {
                                                    param_2 = (char *)DAT_180016928;
                                                    iVar5 = PyDict_SetItem(DAT_180016730,
                                                                           DAT_180016928,
                                                                           DAT_180016c08);
                                                    if (iVar5 < 0) {
                                                      iVar4 = 0x53;
                                                      puVar13 = PTR_s__security_crypto_py_180011d38;
                                                    }
                                                    else {
                                                      plVar7 = (longlong *)
                                                               FUN_18000ced0(0x180015cb0,param_2,
                                                                             (int *)DAT_180016ae0,
                                                                             uVar6,DAT_180016b00,
                                                                             DAT_180016730,
                                                                             DAT_180016898);
                                                      if (plVar7 != (longlong *)0x0) {
                                                        param_2 = (char *)DAT_180016ae0;
                                                        iVar5 = PyDict_SetItem(DAT_180016730,
                                                                               DAT_180016ae0,plVar7)
                                                        ;
                                                        if (iVar5 < 0) {
                                                          iVar4 = 0x56;
                                                        }
                                                        else {
                                                          if ((-1 < (int)*plVar7) &&
                                                             (*plVar7 = *plVar7 + -1, *plVar7 == 0))
                                                          {
                                                            _Py_Dealloc(plVar7);
                                                          }
                                                          plVar7 = (longlong *)
                                                                   FUN_18000ced0(0x180015a68,param_2
                                                                                 ,(int *)
                                                  DAT_1800169d0,uVar6,DAT_180016b00,DAT_180016730,
                                                  DAT_1800168a0);
                                                  if (plVar7 == (longlong *)0x0) {
                                                    iVar4 = 0x5a;
                                                    puVar13 = PTR_s__security_crypto_py_180011d38;
                                                    goto LAB_180009315;
                                                  }
                                                  param_2 = (char *)DAT_1800169d0;
                                                  iVar5 = PyDict_SetItem(DAT_180016730,DAT_1800169d0
                                                                         ,plVar7);
                                                  if (iVar5 < 0) {
                                                    iVar4 = 0x5a;
                                                  }
                                                  else {
                                                    if ((-1 < (int)*plVar7) &&
                                                       (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                                      _Py_Dealloc(plVar7);
                                                    }
                                                    plVar7 = (longlong *)
                                                             FUN_18000ced0(0x180015c90,param_2,
                                                                           (int *)DAT_1800169a0,
                                                                           uVar6,DAT_180016b00,
                                                                           DAT_180016730,
                                                                           DAT_1800168a8);
                                                    if (plVar7 == (longlong *)0x0) {
                                                      iVar4 = 0x69;
                                                      puVar13 = PTR_s__security_crypto_py_180011d38;
                                                      goto LAB_180009315;
                                                    }
                                                    param_2 = (char *)DAT_1800169a0;
                                                    iVar5 = PyDict_SetItem(DAT_180016730,
                                                                           DAT_1800169a0,plVar7);
                                                    if (iVar5 < 0) {
                                                      iVar4 = 0x69;
                                                    }
                                                    else {
                                                      if ((-1 < (int)*plVar7) &&
                                                         (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                                        _Py_Dealloc(plVar7);
                                                      }
                                                      plVar7 = (longlong *)
                                                               FUN_18000ced0(0x180015a88,param_2,
                                                                             (int *)DAT_180016a30,
                                                                             uVar6,DAT_180016b00,
                                                                             DAT_180016730,
                                                                             DAT_1800168b0);
                                                      if (plVar7 == (longlong *)0x0) {
                                                        iVar4 = 0x7f;
                                                        puVar13 = 
                                                  PTR_s__security_crypto_py_180011d38;
                                                  goto LAB_180009315;
                                                  }
                                                  param_2 = (char *)DAT_180016a30;
                                                  iVar5 = PyDict_SetItem(DAT_180016730,DAT_180016a30
                                                                         ,plVar7);
                                                  if (iVar5 < 0) {
                                                    iVar4 = 0x7f;
                                                  }
                                                  else {
                                                    if ((-1 < (int)*plVar7) &&
                                                       (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                                      _Py_Dealloc(plVar7);
                                                    }
                                                    plVar7 = (longlong *)PyDict_New();
                                                    puVar13 = PTR_s__security_crypto_py_180011d38;
                                                    if (plVar7 == (longlong *)0x0)
                                                    goto LAB_180009315;
                                                    param_2 = (char *)DAT_180016b40;
                                                    iVar5 = PyDict_SetItem(DAT_180016730,
                                                                           DAT_180016b40,plVar7);
                                                    if (-1 < iVar5) {
                                                      if ((-1 < (int)*plVar7) &&
                                                         (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
                                                        _Py_Dealloc(plVar7);
                                                      }
                                                      goto LAB_18000938c;
                                                    }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  goto LAB_1800092d4;
                                                  }
                                                  iVar4 = 0x56;
                                                  puVar13 = PTR_s__security_crypto_py_180011d38;
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                }
                                              }
                                            }
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
LAB_180009315:
  if (DAT_180016de0 == (longlong *)0x0) {
    lVar8 = PyErr_Occurred();
    if (lVar8 == 0) {
      PyErr_SetString(*(undefined8 *)PyExc_ImportError_exref,"init _security_crypto");
    }
  }
  else {
    if ((DAT_180016730 != (int *)0x0) && (bVar1)) {
      FUN_18000d220("init _security_crypto",param_2,iVar4,puVar13);
    }
    plVar7 = DAT_180016de0;
    if (((DAT_180016de0 != (longlong *)0x0) && (DAT_180016de0 = (longlong *)0x0, -1 < (int)*plVar7))
       && (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
      _Py_Dealloc();
    }
  }
LAB_18000938c:
  return (DAT_180016de0 != (longlong *)0x0) - 1;
}



// ==== FUN_1800093f0 @ 1800093f0 ====

undefined8 FUN_1800093f0(longlong param_1)

{
  byte bVar1;
  longlong *plVar2;
  longlong *plVar3;
  longlong *plVar4;
  longlong *plVar5;
  longlong *plVar6;
  longlong lVar7;
  ulonglong uVar8;
  char *pcVar9;
  longlong lVar10;
  ulonglong uVar11;
  uint uVar12;
  ulonglong uVar13;
  longlong local_res10 [3];
  char local_208 [16];
  undefined4 local_1f8;
  undefined4 local_1f4;
  undefined4 local_1f0;
  undefined4 local_1ec;
  undefined4 local_1e8;
  undefined4 local_1e4;
  undefined4 local_1e0;
  undefined4 local_1dc;
  undefined4 local_1d8;
  undefined4 local_1d4;
  undefined4 local_1d0;
  undefined4 local_1cc;
  undefined4 local_1c8;
  undefined4 local_1c4;
  undefined4 local_1c0;
  undefined4 local_1bc;
  undefined4 local_1b8;
  undefined4 local_1b4;
  undefined4 local_1b0;
  undefined4 local_1ac;
  undefined4 local_1a8;
  undefined4 local_1a4;
  undefined4 local_1a0;
  undefined4 local_19c;
  undefined4 local_198;
  undefined4 local_194;
  undefined4 local_190;
  undefined4 local_18c;
  undefined4 local_188;
  undefined4 local_184;
  undefined4 local_180;
  undefined4 local_17c;
  undefined4 local_178;
  undefined4 local_174;
  undefined4 local_170;
  undefined4 local_16c;
  undefined4 local_168;
  undefined4 local_164;
  undefined4 local_160;
  undefined4 local_15c;
  undefined4 local_158;
  undefined4 local_154;
  undefined4 local_150;
  undefined4 local_14c;
  undefined4 local_148;
  undefined4 local_144;
  undefined4 local_140;
  undefined4 local_13c;
  undefined4 local_138;
  undefined4 local_134;
  undefined4 local_130;
  undefined4 local_12c;
  undefined4 local_128;
  undefined4 local_124;
  undefined4 local_120;
  undefined4 local_11c;
  undefined4 local_118;
  undefined4 local_114;
  undefined4 local_110;
  undefined4 local_10c;
  undefined4 local_108;
  undefined4 local_104;
  undefined4 local_100;
  undefined4 local_fc;
  undefined4 local_f8;
  undefined4 local_f4;
  undefined4 local_f0;
  undefined4 local_ec;
  undefined4 local_e8;
  undefined4 local_e4;
  undefined4 local_e0;
  undefined4 local_dc;
  undefined4 local_d8;
  undefined4 local_d4;
  undefined4 local_d0;
  undefined4 local_cc;
  undefined4 local_c8;
  undefined4 local_c4;
  undefined4 local_c0;
  undefined4 local_bc;
  undefined4 local_b8;
  undefined4 local_b4;
  undefined4 local_b0;
  undefined4 local_ac;
  undefined4 local_a8;
  undefined4 local_a4;
  undefined4 local_a0;
  undefined4 local_9c;
  undefined4 local_98;
  undefined4 local_94;
  undefined4 local_90;
  undefined8 local_8c;
  undefined4 local_84;
  undefined4 local_80;
  undefined4 local_7c;
  undefined4 local_78;
  undefined4 local_74;
  undefined4 local_70;
  undefined4 local_6c;
  undefined4 local_68;
  undefined4 local_64;
  undefined4 local_60;
  undefined4 local_5c;
  undefined4 local_58;
  undefined4 local_54;
  undefined4 local_50;
  undefined4 local_4c;
  undefined4 local_48;
  
  local_1f8 = 1;
  local_1f4 = 4;
  local_1f0 = 1;
  local_1ec = 7;
  local_1e8 = 6;
  local_1e4 = 2;
  local_1e0 = 9;
  local_1dc = 0xd;
  local_1d8 = 0x13;
  local_1d4 = 0x12;
  local_1d0 = 10;
  local_1cc = 6;
  local_1c8 = 0xf;
  local_1c4 = 0xd;
  local_1c0 = 10;
  local_1bc = 0x14;
  local_1b8 = 0x12;
  local_1b4 = 1;
  local_1b0 = 6;
  local_1ac = 0x11;
  local_1a8 = 0x12;
  local_1a4 = 5;
  local_1a0 = 8;
  local_19c = 10;
  local_198 = 4;
  local_194 = 10;
  local_190 = 0xc;
  local_18c = 0x1d;
  local_188 = 0x11;
  local_184 = 0xb;
  local_180 = 9;
  local_17c = 6;
  local_178 = 8;
  local_174 = 0xc;
  local_170 = 0x1d;
  local_16c = 0xb;
  local_168 = 9;
  local_164 = 9;
  local_160 = 8;
  local_15c = 7;
  local_158 = 9;
  local_154 = 7;
  local_150 = 7;
  local_14c = 8;
  local_148 = 1;
  local_144 = 0xd;
  local_140 = 0xc;
  local_13c = 0x10;
  local_138 = 5;
  local_134 = 3;
  local_130 = 7;
  local_12c = 2;
  local_128 = 5;
  local_124 = 6;
  local_120 = 4;
  local_11c = 7;
  local_118 = 3;
  local_114 = 0xc;
  local_110 = 8;
  local_10c = 10;
  local_108 = 8;
  local_104 = 4;
  local_100 = 4;
  local_fc = 5;
  local_f8 = 2;
  local_f4 = 3;
  local_f0 = 7;
  local_ec = 8;
  local_e8 = 3;
  local_e4 = 0xf;
  local_e0 = 0xc;
  local_dc = 3;
  local_d8 = 0xc;
  local_d4 = 0x10;
  local_d0 = 4;
  local_cc = 0xc;
  local_c8 = 10;
  local_c4 = 6;
  local_c0 = 3;
  local_bc = 9;
  local_b8 = 10;
  local_b4 = 8;
  uVar13 = 0;
  local_b0 = 5;
  local_ac = 8;
  local_a8 = 7;
  local_a4 = 4;
  local_a0 = 5;
  local_9c = 6;
  local_98 = 9;
  local_94 = 4;
  local_90 = 0x10;
  local_8c = 0x20;
  local_84 = 0x1f;
  local_80 = 0x16;
  local_7c = 2;
  local_78 = 0xc3;
  local_74 = 2;
  local_70 = 0x11;
  local_6c = 0x61;
  local_68 = 0x34;
  local_64 = 0x27;
  local_60 = 0x56;
  local_5c = 0x5f;
  local_58 = 0xfc;
  local_54 = 0x10;
  local_50 = 4;
  local_4c = 3;
  local_48 = 0x17;
  plVar2 = (longlong *)PyUnicode_FromString("decompress");
  if (plVar2 == (longlong *)0x0) {
    return 0xffffffff;
  }
  plVar3 = (longlong *)PyImport_ImportModule(&DAT_180011c40);
  if ((plVar3 == (longlong *)0x0) ||
     (plVar4 = (longlong *)PyObject_GetAttr(plVar3,plVar2), plVar4 == (longlong *)0x0)) {
    PyErr_Format(*(undefined8 *)PyExc_ImportError_exref,
                 "Failed to import \'%.20s.decompress\' - cannot initialise module strings. String compression was configured with the C macro \'CYTHON_COMPRESS_STRINGS=%d\'."
                 ,&DAT_180011c40,1);
    if (plVar3 != (longlong *)0x0) goto LAB_1800099d0;
  }
  else {
    plVar5 = (longlong *)PyMemoryView_FromMemory(&DAT_180010bd0,0x430,0x100);
    if (plVar5 != (longlong *)0x0) {
      plVar6 = (longlong *)PyObject_CallFunctionObjArgs(plVar4,plVar5,0);
      if ((-1 < (int)*plVar5) && (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
        _Py_Dealloc(plVar5);
      }
      if ((-1 < (int)*plVar4) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)) {
        _Py_Dealloc(plVar4);
      }
      if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
        _Py_Dealloc(plVar3);
      }
      if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
        _Py_Dealloc(plVar2);
      }
      uVar8 = uVar13;
      uVar11 = uVar13;
      if (plVar6 == (longlong *)0x0) {
        return 0xffffffff;
      }
      do {
        bVar1 = *(byte *)(&local_1f8 + uVar8);
        local_res10[0] = PyUnicode_DecodeUTF8((longlong)plVar6 + uVar11 + 0x20,(ulonglong)bVar1,0);
        if (local_res10[0] == 0) goto LAB_180009997;
        if (9 < uVar8) {
          PyUnicode_InternInPlace(local_res10);
        }
        if (local_res10[0] == 0) goto LAB_180009997;
        *(longlong *)(param_1 + 0x188 + uVar8 * 8) = local_res10[0];
        uVar11 = uVar11 + bVar1;
        uVar8 = uVar8 + 1;
      } while ((longlong)uVar8 < 0x5a);
      lVar10 = 0x5a;
      while( true ) {
        bVar1 = *(byte *)(&local_1f8 + lVar10);
        lVar7 = PyBytes_FromStringAndSize((longlong)plVar6 + uVar11 + 0x20,(ulonglong)bVar1);
        uVar11 = uVar11 + bVar1;
        *(longlong *)(param_1 + 0x188 + lVar10 * 8) = lVar7;
        if (lVar7 == 0) break;
        lVar10 = lVar10 + 1;
        if (0x6c < lVar10) {
          uVar8 = uVar13;
          if ((-1 < (int)*plVar6) && (*plVar6 = *plVar6 + -1, *plVar6 == 0)) {
            _Py_Dealloc(plVar6);
          }
          do {
            lVar10 = PyObject_Hash(*(undefined8 *)(param_1 + 0x188 + uVar8 * 8));
            if (lVar10 == -1) {
              return 0xffffffff;
            }
            uVar8 = uVar8 + 1;
          } while ((longlong)uVar8 < 0x6d);
          local_208[0] = '\0';
          local_208[1] = '\x01';
          local_208[2] = '\x03';
          local_208[3] = '\x04';
          pcVar9 = local_208;
          local_208[4] = '\x06';
          local_208[5] = -0x10;
          local_208[6] = '\x10';
          local_208[7] = '\x14';
          plVar2 = (longlong *)(param_1 + 0x4f0);
          local_208[8] = 0x20;
          do {
            lVar10 = PyLong_FromLong((int)*pcVar9);
            *plVar2 = lVar10;
            if (lVar10 == 0) {
              return 0xffffffff;
            }
            uVar12 = (int)uVar13 + 1;
            uVar13 = (ulonglong)uVar12;
            pcVar9 = pcVar9 + 1;
            plVar2 = plVar2 + 1;
          } while ((int)uVar12 < 9);
          return 0;
        }
      }
LAB_180009997:
      if ((int)*plVar6 < 0) {
        return 0xffffffff;
      }
      *plVar6 = *plVar6 + -1;
      lVar10 = *plVar6;
      plVar2 = plVar6;
      goto joined_r0x0001800099a0;
    }
    if ((-1 < (int)*plVar4) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)) {
      _Py_Dealloc(plVar4);
    }
LAB_1800099d0:
    if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
      _Py_Dealloc(plVar3);
    }
  }
  if ((int)*plVar2 < 0) {
    return 0xffffffff;
  }
  *plVar2 = *plVar2 + -1;
  lVar10 = *plVar2;
joined_r0x0001800099a0:
  if (lVar10 == 0) {
    _Py_Dealloc(plVar2);
  }
  return 0xffffffff;
}



// ==== FUN_180009a20 @ 180009a20 ====

undefined8 FUN_180009a20(longlong param_1)

{
  undefined8 uVar1;
  undefined8 uVar2;
  undefined8 uVar3;
  longlong *plVar4;
  longlong *plVar5;
  longlong extraout_RAX;
  longlong extraout_RAX_00;
  longlong extraout_RAX_01;
  longlong extraout_RAX_02;
  longlong extraout_RAX_03;
  longlong extraout_RAX_04;
  longlong extraout_RAX_05;
  longlong extraout_RAX_06;
  longlong extraout_RAX_07;
  longlong extraout_RAX_08;
  longlong extraout_RAX_09;
  longlong extraout_RAX_10;
  longlong *plVar6;
  undefined8 local_78;
  undefined8 local_70;
  
  plVar5 = (longlong *)PyDict_New();
  if (plVar5 != (longlong *)0x0) {
    local_78 = *(undefined8 *)(param_1 + 0x2e8);
    local_70 = *(undefined8 *)(param_1 + 0x210);
    plVar6 = FUN_18000ed60(0x461190,&local_78,*(undefined8 *)(param_1 + 0x1c8),
                           *(undefined8 *)(param_1 + 0x2c0),*(longlong **)(param_1 + 0x480),plVar5);
    DAT_180016858 = extraout_RAX;
    if (extraout_RAX != 0) {
      uVar1 = *(undefined8 *)(param_1 + 0x2c0);
      uVar2 = *(undefined8 *)(param_1 + 0x1c8);
      *(undefined8 *)((longlong)plVar6 + -0x19) = *(undefined8 *)(param_1 + 0x2e8);
      *(undefined8 *)((longlong)plVar6 + -0x11) = *(undefined8 *)(param_1 + 0x210);
      plVar6 = FUN_18000ed60(0x621190,(undefined8 *)((longlong)plVar6 + -0x19),uVar2,uVar1,
                             *(longlong **)(param_1 + 0x490),plVar5);
      DAT_180016860 = extraout_RAX_00;
      if (extraout_RAX_00 != 0) {
        uVar1 = *(undefined8 *)(param_1 + 0x350);
        uVar2 = *(undefined8 *)(param_1 + 0x1c8);
        *(undefined8 *)((longlong)plVar6 + -0x19) = *(undefined8 *)(param_1 + 0x2e0);
        *(undefined8 *)((longlong)plVar6 + -0x11) = *(undefined8 *)(param_1 + 0x348);
        *(undefined8 *)((longlong)plVar6 + -9) = *(undefined8 *)(param_1 + 0x3c0);
        plVar6 = FUN_18000ed60(0x1c0198,(undefined8 *)((longlong)plVar6 + -0x19),uVar2,uVar1,
                               *(longlong **)(param_1 + 0x4a0),plVar5);
        DAT_180016868 = extraout_RAX_01;
        if (extraout_RAX_01 != 0) {
          uVar1 = *(undefined8 *)(param_1 + 0x290);
          uVar2 = *(undefined8 *)(param_1 + 0x1c8);
          *(undefined8 *)((longlong)plVar6 + 7) = *(undefined8 *)(param_1 + 0x248);
          *(undefined8 *)((longlong)plVar6 + 0xf) = *(undefined8 *)(param_1 + 0x240);
          *(undefined8 *)((longlong)plVar6 + 0x17) = *(undefined8 *)(param_1 + 0x310);
          *(undefined8 *)((longlong)plVar6 + 0x1f) = *(undefined8 *)(param_1 + 0x318);
          *(undefined8 *)((longlong)plVar6 + 0x27) = *(undefined8 *)(param_1 + 0x2a8);
          uVar3 = *(undefined8 *)(param_1 + 0x2c0);
          *(undefined8 *)((longlong)plVar6 + 0x2f) = uVar3;
          *(undefined8 *)((longlong)plVar6 + 0x37) = uVar3;
          plVar6 = FUN_18000ed60(0x3801b9,(undefined8 *)((longlong)plVar6 + 7),uVar2,uVar1,
                                 *(longlong **)(param_1 + 0x4b8),plVar5);
          DAT_180016870 = extraout_RAX_02;
          if (extraout_RAX_02 != 0) {
            uVar1 = *(undefined8 *)(param_1 + 600);
            uVar2 = *(undefined8 *)(param_1 + 0x1c8);
            *(undefined8 *)((longlong)plVar6 + 7) = *(undefined8 *)(param_1 + 0x248);
            *(undefined8 *)((longlong)plVar6 + 0xf) = *(undefined8 *)(param_1 + 0x398);
            *(undefined8 *)((longlong)plVar6 + 0x17) = *(undefined8 *)(param_1 + 0x310);
            *(undefined8 *)((longlong)plVar6 + 0x1f) = *(undefined8 *)(param_1 + 0x318);
            *(undefined8 *)((longlong)plVar6 + 0x27) = *(undefined8 *)(param_1 + 0x278);
            uVar3 = *(undefined8 *)(param_1 + 0x2c0);
            *(undefined8 *)((longlong)plVar6 + 0x2f) = uVar3;
            *(undefined8 *)((longlong)plVar6 + 0x37) = uVar3;
            plVar6 = FUN_18000ed60(0x5201b9,(undefined8 *)((longlong)plVar6 + 7),uVar2,uVar1,
                                   *(longlong **)(param_1 + 0x4c0),plVar5);
            DAT_180016878 = extraout_RAX_03;
            if (extraout_RAX_03 != 0) {
              uVar1 = *(undefined8 *)(param_1 + 0x268);
              uVar2 = *(undefined8 *)(param_1 + 0x1c8);
              *(undefined8 *)((longlong)plVar6 + 0x6f) = *(undefined8 *)(param_1 + 0x248);
              plVar6 = FUN_18000ed60(0x6a0189,(undefined8 *)((longlong)plVar6 + 0x6f),uVar2,uVar1,
                                     *(longlong **)(param_1 + 0x4a8),plVar5);
              DAT_180016880 = extraout_RAX_04;
              if (extraout_RAX_04 != 0) {
                uVar1 = *(undefined8 *)(param_1 + 0x2f8);
                uVar2 = *(undefined8 *)(param_1 + 0x1c8);
                *(undefined8 *)((longlong)plVar6 + 0x6f) = *(undefined8 *)(param_1 + 0x248);
                plVar6 = FUN_18000ed60(0x800189,(undefined8 *)((longlong)plVar6 + 0x6f),uVar2,uVar1,
                                       *(longlong **)(param_1 + 0x4b0),plVar5);
                DAT_180016888 = extraout_RAX_05;
                if (extraout_RAX_05 != 0) {
                  plVar4 = *(longlong **)(param_1 + 0x498);
                  uVar1 = *(undefined8 *)(param_1 + 0x448);
                  uVar2 = *(undefined8 *)(param_1 + 0x1c8);
                  *(undefined8 *)((longlong)plVar6 + 0x6f) = 0;
                  plVar6 = FUN_18000ed60(0x8c0180,(undefined8 *)((longlong)plVar6 + 0x6f),uVar2,
                                         uVar1,plVar4,plVar5);
                  DAT_180016890 = extraout_RAX_06;
                  if (extraout_RAX_06 != 0) {
                    plVar4 = *(longlong **)(param_1 + 0x478);
                    uVar1 = *(undefined8 *)(param_1 + 0x3b0);
                    uVar2 = *(undefined8 *)(param_1 + 0x1c8);
                    *(undefined8 *)((longlong)plVar6 + 0x6f) = 0;
                    plVar6 = FUN_18000ed60(0xac0180,(undefined8 *)((longlong)plVar6 + 0x6f),uVar2,
                                           uVar1,plVar4,plVar5);
                    DAT_180016898 = extraout_RAX_07;
                    if (extraout_RAX_07 != 0) {
                      uVar1 = *(undefined8 *)(param_1 + 0x2a0);
                      uVar2 = *(undefined8 *)(param_1 + 0x1c8);
                      *(undefined8 *)((longlong)plVar6 + 7) = *(undefined8 *)(param_1 + 0x3c8);
                      *(undefined8 *)((longlong)plVar6 + 0xf) = *(undefined8 *)(param_1 + 0x390);
                      *(undefined8 *)((longlong)plVar6 + 0x17) = *(undefined8 *)(param_1 + 0x310);
                      *(undefined8 *)((longlong)plVar6 + 0x1f) = *(undefined8 *)(param_1 + 0x380);
                      *(undefined8 *)((longlong)plVar6 + 0x27) = *(undefined8 *)(param_1 + 0x2a8);
                      *(undefined8 *)((longlong)plVar6 + 0x2f) = *(undefined8 *)(param_1 + 800);
                      *(undefined8 *)((longlong)plVar6 + 0x37) = *(undefined8 *)(param_1 + 0x2e8);
                      *(undefined8 *)((longlong)plVar6 + 0x3f) = *(undefined8 *)(param_1 + 0x3f8);
                      plVar6 = FUN_18000ed60(0xb401c1,(undefined8 *)((longlong)plVar6 + 7),uVar2,
                                             uVar1,*(longlong **)(param_1 + 0x488),plVar5);
                      DAT_1800168a0 = extraout_RAX_08;
                      if (extraout_RAX_08 != 0) {
                        uVar1 = *(undefined8 *)(param_1 + 0x270);
                        uVar2 = *(undefined8 *)(param_1 + 0x1c8);
                        *(undefined8 *)((longlong)plVar6 + 7) = *(undefined8 *)(param_1 + 0x288);
                        *(undefined8 *)((longlong)plVar6 + 0xf) = *(undefined8 *)(param_1 + 0x380);
                        *(undefined8 *)((longlong)plVar6 + 0x17) = *(undefined8 *)(param_1 + 0x408);
                        *(undefined8 *)((longlong)plVar6 + 0x1f) = *(undefined8 *)(param_1 + 0x218);
                        *(undefined8 *)((longlong)plVar6 + 0x27) = *(undefined8 *)(param_1 + 0x310);
                        *(undefined8 *)((longlong)plVar6 + 0x2f) = *(undefined8 *)(param_1 + 0x400);
                        *(undefined8 *)((longlong)plVar6 + 0x37) = *(undefined8 *)(param_1 + 0x278);
                        *(undefined8 *)((longlong)plVar6 + 0x3f) = *(undefined8 *)(param_1 + 800);
                        *(undefined8 *)((longlong)plVar6 + 0x47) = *(undefined8 *)(param_1 + 0x2e8);
                        plVar6 = FUN_18000ed60(0xd201c9,(undefined8 *)((longlong)plVar6 + 7),uVar2,
                                               uVar1,*(longlong **)(param_1 + 0x4c8),plVar5);
                        DAT_1800168a8 = extraout_RAX_09;
                        if (extraout_RAX_09 != 0) {
                          uVar1 = *(undefined8 *)(param_1 + 0x300);
                          uVar2 = *(undefined8 *)(param_1 + 0x1c8);
                          *(undefined8 *)((longlong)plVar6 + 0x6f) =
                               *(undefined8 *)(param_1 + 0x248);
                          FUN_18000ed60(0xfe0189,(undefined8 *)((longlong)plVar6 + 0x6f),uVar2,uVar1
                                        ,*(longlong **)(param_1 + 0x470),plVar5);
                          DAT_1800168b0 = extraout_RAX_10;
                          if (extraout_RAX_10 != 0) {
                            if ((-1 < (int)*plVar5) && (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
                              _Py_Dealloc(plVar5);
                            }
                            return 0;
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    if ((-1 < (int)*plVar5) && (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
      _Py_Dealloc(plVar5);
    }
  }
  return 0xffffffff;
}



// ==== FUN_180009f30 @ 180009f30 ====

undefined8 FUN_180009f30(undefined *param_1,longlong param_2)

{
  longlong lVar1;
  longlong lVar2;
  longlong lVar3;
  uint uVar4;
  longlong *plVar5;
  code *pcVar6;
  code *pcVar7;
  undefined8 uVar8;
  longlong lVar9;
  longlong lVar10;
  longlong *plVar11;
  code *pcVar12;
  longlong lVar13;
  code *pcVar14;
  
  lVar1 = *(longlong *)(param_2 + 0x10);
  lVar13 = 0;
  if (lVar1 < 1) {
LAB_18000a116:
    uVar8 = 0;
  }
  else {
    plVar11 = (longlong *)(param_2 + 0x18);
    plVar5 = plVar11;
    do {
      if (param_1 == (undefined *)*plVar5) goto LAB_18000a133;
      lVar13 = lVar13 + 1;
      plVar5 = plVar5 + 1;
    } while (lVar13 < lVar1);
    lVar13 = 0;
    pcVar12 = PyBaseObject_Type_exref;
LAB_180009f82:
    pcVar14 = (code *)*plVar11;
    if ((code *)param_1 != pcVar14) {
      if ((*(int *)(*(longlong *)(param_1 + 8) + 0xa8) < 0) &&
         ((*(uint *)(param_1 + 0xa8) & 0x40000000) != 0)) {
        if (((int)*(uint *)(*(longlong *)(pcVar14 + 8) + 0xa8) < 0) &&
           ((*(uint *)(pcVar14 + 0xa8) & 0x40000000) != 0)) {
          lVar2 = *(longlong *)(param_1 + 0x158);
          pcVar6 = (code *)param_1;
          if (lVar2 == 0) {
            do {
              pcVar6 = *(code **)(pcVar6 + 0x100);
              if (pcVar6 == pcVar14) goto LAB_18000a01f;
            } while (pcVar6 != (code *)0x0);
            uVar4 = (uint)(pcVar14 == pcVar12);
          }
          else {
            lVar9 = 0;
            if (*(longlong *)(lVar2 + 0x10) < 1) goto LAB_18000a0ee;
            plVar5 = (longlong *)(lVar2 + 0x18);
            do {
              if ((code *)*plVar5 == pcVar14) goto LAB_18000a01f;
              lVar9 = lVar9 + 1;
              plVar5 = plVar5 + 1;
            } while (lVar9 < *(longlong *)(lVar2 + 0x10));
            uVar4 = 0;
          }
        }
        else {
          if ((*(uint *)(*(longlong *)(pcVar14 + 8) + 0xa8) >> 0x1a & 1) == 0) goto LAB_18000a0f2;
          lVar2 = *(longlong *)(pcVar14 + 0x10);
          lVar9 = 0;
          if (0 < lVar2) {
            pcVar6 = pcVar14 + 0x18;
            do {
              if (param_1 == *(undefined **)pcVar6) goto LAB_18000a01f;
              lVar9 = lVar9 + 1;
              pcVar6 = pcVar6 + 8;
            } while (lVar9 < lVar2);
            lVar9 = 0;
            pcVar14 = pcVar14 + 0x18;
            do {
              pcVar6 = *(code **)pcVar14;
              if ((*(int *)(*(longlong *)(pcVar6 + 8) + 0xa8) < 0) &&
                 ((*(uint *)(pcVar6 + 0xa8) & 0x40000000) != 0)) {
                if ((code *)param_1 == pcVar6) goto LAB_18000a01f;
                lVar3 = *(longlong *)(param_1 + 0x158);
                pcVar7 = (code *)param_1;
                if (lVar3 == 0) {
                  do {
                    pcVar7 = *(code **)(pcVar7 + 0x100);
                    if (pcVar7 == pcVar6) goto LAB_18000a01f;
                  } while (pcVar7 != (code *)0x0);
                  if (pcVar6 == pcVar12) goto LAB_18000a01f;
                }
                else {
                  lVar10 = 0;
                  if (0 < *(longlong *)(lVar3 + 0x10)) {
                    plVar5 = (longlong *)(lVar3 + 0x18);
                    do {
                      if ((code *)*plVar5 == pcVar6) goto LAB_18000a01f;
                      lVar10 = lVar10 + 1;
                      plVar5 = plVar5 + 1;
                    } while (lVar10 < *(longlong *)(lVar3 + 0x10));
                  }
                }
              }
              lVar9 = lVar9 + 1;
              pcVar14 = pcVar14 + 8;
            } while (lVar9 < lVar2);
          }
LAB_18000a0ee:
          uVar4 = 0;
        }
      }
      else {
LAB_18000a0f2:
        uVar4 = PyErr_GivenExceptionMatches(param_1);
        pcVar12 = PyBaseObject_Type_exref;
      }
      goto LAB_18000a102;
    }
LAB_18000a133:
    uVar8 = 1;
  }
  return uVar8;
LAB_18000a01f:
  uVar4 = 1;
LAB_18000a102:
  if (uVar4 != 0) goto LAB_18000a133;
  lVar13 = lVar13 + 1;
  plVar11 = plVar11 + 1;
  if (lVar1 <= lVar13) goto LAB_18000a116;
  goto LAB_180009f82;
}



// ==== FUN_18000a140 @ 18000a140 ====

int * FUN_18000a140(longlong param_1)

{
  int *piVar1;
  longlong lVar2;
  int *local_res8 [4];
  
  piVar1 = (int *)_PyDict_GetItem_KnownHash(DAT_180016730,param_1,*(undefined8 *)(param_1 + 0x18));
  if (piVar1 == (int *)0x0) {
    PyErr_Clear();
    PyObject_GetOptionalAttr(DAT_180016738,param_1,local_res8);
    if ((local_res8[0] == (int *)0x0) && (lVar2 = PyErr_Occurred(), lVar2 == 0)) {
      PyErr_Format(*(undefined8 *)PyExc_NameError_exref,"name \'%U\' is not defined",param_1);
    }
  }
  else {
    local_res8[0] = piVar1;
    if (*piVar1 + 1 != 0) {
      *piVar1 = *piVar1 + 1;
      return piVar1;
    }
  }
  return local_res8[0];
}



// ==== FUN_18000a1d0 @ 18000a1d0 ====

longlong FUN_18000a1d0(longlong param_1,undefined8 param_2,undefined8 param_3)

{
  code *pcVar1;
  int iVar2;
  longlong lVar3;
  longlong lVar4;
  
  pcVar1 = *(code **)(*(longlong *)(param_1 + 8) + 0x80);
  if (pcVar1 == (code *)0x0) {
    lVar3 = PyObject_Call();
  }
  else {
    iVar2 = Py_EnterRecursiveCall(" while calling a Python object");
    if (iVar2 == 0) {
      lVar3 = (*pcVar1)(param_1,param_2,param_3);
      Py_LeaveRecursiveCall();
      if ((lVar3 == 0) && (lVar4 = PyErr_Occurred(), lVar4 == 0)) {
        PyErr_SetString(*(undefined8 *)PyExc_SystemError_exref,
                        "NULL result without error in PyObject_Call");
      }
    }
    else {
      lVar3 = 0;
    }
  }
  return lVar3;
}



// ==== FUN_18000a270 @ 18000a270 ====

longlong FUN_18000a270(longlong param_1,undefined8 param_2)

{
  code *pcVar1;
  int iVar2;
  longlong lVar3;
  longlong lVar4;
  undefined8 uVar5;
  
  pcVar1 = *(code **)(*(longlong *)(param_1 + 0x10) + 8);
  if ((*(byte *)(*(longlong *)(param_1 + 0x10) + 0x10) & 0x20) == 0) {
    uVar5 = *(undefined8 *)(param_1 + 0x18);
  }
  else {
    uVar5 = 0;
  }
  iVar2 = Py_EnterRecursiveCall(" while calling a Python object");
  if (iVar2 != 0) {
    return 0;
  }
  lVar3 = (*pcVar1)(uVar5,param_2);
  Py_LeaveRecursiveCall();
  if (lVar3 == 0) {
    lVar4 = PyErr_Occurred();
    if (lVar4 == 0) {
      PyErr_SetString(*(undefined8 *)PyExc_SystemError_exref,
                      "NULL result without error in PyObject_Call");
    }
  }
  return lVar3;
}



// ==== FUN_18000a310 @ 18000a310 ====

void FUN_18000a310(longlong param_1,undefined8 *param_2,ulonglong param_3,longlong param_4)

{
  undefined *puVar1;
  undefined8 uVar2;
  longlong lVar3;
  ulonglong uVar4;
  
  uVar4 = param_3 & 0x7fffffffffffffff;
  if (uVar4 == 0) {
    if (param_4 == 0) {
      uVar2 = FUN_18000d470(*(undefined **)(param_1 + 8),DAT_180016d90,PyCFunction_Type_exref);
      if (((int)uVar2 != 0) && ((*(byte *)(*(longlong *)(param_1 + 0x10) + 0x10) & 4) != 0)) {
        FUN_18000a270(param_1,0);
        return;
      }
LAB_18000a3c1:
      puVar1 = *(undefined **)(param_1 + 8);
      if (puVar1 == DAT_180016d90) {
        lVar3 = 0x30;
LAB_18000a3e5:
        if (*(code **)(param_1 + lVar3) != (code *)0x0) {
          (**(code **)(param_1 + lVar3))(param_1,param_2,param_3,0);
          return;
        }
      }
      else if ((*(uint *)(puVar1 + 0xa8) & 0x800) != 0) {
        lVar3 = *(longlong *)(puVar1 + 0x38);
        goto LAB_18000a3e5;
      }
      if (uVar4 != 0) goto LAB_18000a418;
    }
    FUN_18000a1d0(param_1,DAT_180016748,param_4);
  }
  else {
    if (param_4 == 0) {
      if (((uVar4 == 1) &&
          (uVar2 = FUN_18000d470(*(undefined **)(param_1 + 8),DAT_180016d90,PyCFunction_Type_exref),
          (int)uVar2 != 0)) && ((*(byte *)(*(longlong *)(param_1 + 0x10) + 0x10) & 8) != 0)) {
        FUN_18000a270(param_1,*param_2);
        return;
      }
      goto LAB_18000a3c1;
    }
LAB_18000a418:
    PyObject_VectorcallDict(param_1,param_2,uVar4,param_4);
  }
  return;
}



// ==== FUN_18000a440 @ 18000a440 ====

longlong * FUN_18000a440(longlong param_1,undefined8 param_2,longlong param_3,uint param_4)

{
  longlong lVar1;
  longlong *plVar2;
  longlong lVar3;
  void *_Src;
  uint uVar4;
  uint uVar5;
  longlong lVar6;
  longlong lVar7;
  byte bVar8;
  longlong lVar9;
  longlong lVar10;
  
  uVar4 = 0x10ffff;
  if (param_4 < 0x110000) {
    uVar4 = param_4;
  }
  plVar2 = (longlong *)PyUnicode_New(param_3,uVar4);
  if (plVar2 == (longlong *)0x0) {
    return (longlong *)0x0;
  }
  if (uVar4 < 0x100) {
    uVar5 = 1;
  }
  else {
    bVar8 = 2;
    uVar5 = 4;
    if (0xffff < uVar4) goto LAB_18000a4a9;
    uVar5 = 2;
  }
  bVar8 = (char)uVar5 - 1;
LAB_18000a4a9:
  if ((*(uint *)(plVar2 + 4) & 0x20) == 0) {
    lVar9 = plVar2[7];
  }
  else {
    lVar9 = (((ulonglong)(~*(uint *)(plVar2 + 4) & 0x40) | 0xa0) >> 2) + (longlong)plVar2;
  }
  lVar10 = 0x7fffffffffffffff >> (bVar8 & 0x3f);
  if (lVar10 - param_3 < 0) {
LAB_18000a582:
    PyErr_SetString(*(undefined8 *)PyExc_OverflowError_exref,
                    "join() result is too long for a Python string");
LAB_18000a599:
    if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
      _Py_Dealloc(plVar2);
    }
    return (longlong *)0x0;
  }
  lVar6 = 0;
  lVar7 = lVar6;
  do {
    lVar3 = *(longlong *)(param_1 + lVar6 * 8);
    lVar1 = *(longlong *)(lVar3 + 0x10);
    if (lVar1 != 0) {
      if (lVar10 - lVar1 < lVar7) goto LAB_18000a582;
      uVar4 = *(uint *)(lVar3 + 0x20);
      if ((uVar4 & 0x20) == 0) {
        _Src = *(void **)(lVar3 + 0x38);
      }
      else {
        _Src = (void *)((((ulonglong)(~uVar4 & 0x40) | 0xa0) >> 2) + lVar3);
      }
      if ((uVar4 >> 2 & 7) == uVar5) {
        memcpy((void *)((lVar7 << (bVar8 & 0x3f)) + lVar9),_Src,lVar1 << (bVar8 & 0x3f));
      }
      else {
        lVar3 = PyUnicode_CopyCharacters(plVar2,lVar7,lVar3,0,lVar1);
        if (lVar3 < 0) goto LAB_18000a599;
      }
      lVar7 = lVar7 + lVar1;
    }
    lVar6 = lVar6 + 1;
    if (3 < lVar6) {
      return plVar2;
    }
  } while( true );
}



// ==== FUN_18000a5d0 @ 18000a5d0 ====

undefined8
FUN_18000a5d0(longlong param_1,undefined8 *param_2,undefined8 *param_3,longlong *param_4,
             undefined8 param_5)

{
  undefined8 *puVar1;
  uint uVar2;
  uint uVar3;
  longlong *plVar4;
  longlong lVar5;
  int iVar6;
  longlong lVar7;
  undefined8 uVar8;
  void *pvVar9;
  void *pvVar10;
  undefined8 *puVar11;
  uint uVar12;
  
  lVar7 = *(longlong *)(param_1 + 0x18);
  if ((lVar7 == -1) && (lVar7 = PyObject_Hash(), lVar7 == -1)) {
LAB_18000a7c7:
    uVar8 = 0xffffffff;
  }
  else {
    plVar4 = (longlong *)*param_3;
    puVar11 = param_3;
    while (plVar4 != (longlong *)0x0) {
      lVar5 = *plVar4;
      if ((lVar7 == *(longlong *)(lVar5 + 0x18)) &&
         (*(longlong *)(lVar5 + 0x10) == *(longlong *)(param_1 + 0x10))) {
        uVar2 = *(uint *)(lVar5 + 0x20);
        uVar3 = *(uint *)(param_1 + 0x20);
        uVar12 = uVar2 >> 2 & 7;
        if (uVar12 == (uVar3 >> 2 & 7)) {
          if ((uVar2 & 0x20) == 0) {
            pvVar9 = *(void **)(lVar5 + 0x38);
          }
          else {
            pvVar9 = (void *)(lVar5 + (((ulonglong)(~uVar2 & 0x40) | 0xa0) >> 2));
          }
          if ((uVar3 & 0x20) == 0) {
            pvVar10 = *(void **)(param_1 + 0x38);
          }
          else {
            pvVar10 = (void *)((((ulonglong)(~uVar3 & 0x40) | 0xa0) >> 2) + param_1);
          }
          iVar6 = memcmp(pvVar9,pvVar10,(ulonglong)uVar12 * *(longlong *)(lVar5 + 0x10));
          if (iVar6 == 0) {
            *param_4 = (longlong)puVar11 - (longlong)param_2 >> 3;
            return 1;
          }
        }
      }
      puVar1 = puVar11 + 1;
      puVar11 = puVar11 + 1;
      plVar4 = (longlong *)*puVar1;
    }
    for (; param_2 != param_3; param_2 = param_2 + 1) {
      lVar5 = *(longlong *)*param_2;
      if ((lVar7 == *(longlong *)(lVar5 + 0x18)) &&
         (*(longlong *)(lVar5 + 0x10) == *(longlong *)(param_1 + 0x10))) {
        uVar2 = *(uint *)(lVar5 + 0x20);
        uVar3 = *(uint *)(param_1 + 0x20);
        uVar12 = uVar2 >> 2 & 7;
        if (uVar12 == (uVar3 >> 2 & 7)) {
          if ((uVar2 & 0x20) == 0) {
            pvVar9 = *(void **)(lVar5 + 0x38);
          }
          else {
            pvVar9 = (void *)((((ulonglong)(~uVar2 & 0x40) | 0xa0) >> 2) + lVar5);
          }
          if ((uVar3 & 0x20) == 0) {
            pvVar10 = *(void **)(param_1 + 0x38);
          }
          else {
            pvVar10 = (void *)((((ulonglong)(~uVar3 & 0x40) | 0xa0) >> 2) + param_1);
          }
          iVar6 = memcmp(pvVar9,pvVar10,(ulonglong)uVar12 * *(longlong *)(lVar5 + 0x10));
          if (iVar6 == 0) {
            PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                         "%s() got multiple values for keyword argument \'%U\'",param_5,param_1);
            goto LAB_18000a7c7;
          }
        }
      }
    }
    uVar8 = 0;
  }
  return uVar8;
}



// ==== FUN_18000a7d0 @ 18000a7d0 ====

void FUN_18000a7d0(undefined8 param_1,longlong *param_2,longlong *param_3,undefined8 param_4)

{
  undefined8 *puVar1;
  longlong lVar2;
  int iVar3;
  undefined8 uVar4;
  longlong *plVar5;
  longlong *plVar6;
  longlong local_38;
  undefined8 local_30;
  longlong local_28 [2];
  
  local_30 = 0;
  local_38 = 0;
  iVar3 = PyDict_Next(param_1,&local_30,&local_38,0);
  lVar2 = local_38;
  do {
    if (iVar3 == 0) {
      return;
    }
    plVar5 = param_3;
    for (plVar6 = (longlong *)*param_3; local_38 = lVar2, plVar6 != (longlong *)0x0;
        plVar6 = (longlong *)*plVar6) {
      if (*plVar6 == lVar2) {
        if (*plVar5 != 0) goto LAB_18000a92a;
        break;
      }
      plVar6 = plVar5 + 1;
      plVar5 = plVar5 + 1;
    }
    local_28[0] = 0;
    if (*(code **)(lVar2 + 8) == PyUnicode_Type_exref) {
      uVar4 = FUN_18000a5d0(lVar2,param_2,param_3,local_28,param_4);
      iVar3 = (int)uVar4;
    }
    else if ((*(uint *)(*(code **)(lVar2 + 8) + 0xa8) & 0x10000000) == 0) {
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() keywords must be strings",param_4)
      ;
      iVar3 = -1;
    }
    else {
      puVar1 = (undefined8 *)*param_3;
      plVar6 = param_3;
      while (puVar1 != (undefined8 *)0x0) {
        iVar3 = PyObject_RichCompareBool(*puVar1,lVar2,2);
        if (iVar3 == 1) {
          iVar3 = 1;
          goto LAB_18000a925;
        }
        if (iVar3 == -1) goto LAB_18000a973;
        plVar5 = plVar6 + 1;
        plVar6 = plVar6 + 1;
        puVar1 = (undefined8 *)*plVar5;
      }
      plVar6 = param_2;
      if (param_2 != param_3) {
LAB_18000a900:
        iVar3 = PyObject_RichCompareBool(*(undefined8 *)*plVar6,lVar2,2);
        if (iVar3 == 0) break;
        if (iVar3 == 1) {
          PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                       "%s() got multiple values for keyword argument \'%U\'",param_4,lVar2);
        }
LAB_18000a973:
        iVar3 = -1;
        goto LAB_18000a925;
      }
LAB_18000a922:
      iVar3 = 0;
    }
LAB_18000a925:
    if (iVar3 != 1) {
      if (iVar3 != 0) {
        return;
      }
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                   "%s() got an unexpected keyword argument \'%U\'",param_4,local_38);
      return;
    }
LAB_18000a92a:
    iVar3 = PyDict_Next(param_1,&local_30,&local_38,0);
    lVar2 = local_38;
  } while( true );
  plVar6 = plVar6 + 1;
  if (plVar6 == param_3) goto LAB_18000a922;
  goto LAB_18000a900;
}



// ==== FUN_18000a9c0 @ 18000a9c0 ====

undefined8
FUN_18000a9c0(longlong param_1,undefined8 *param_2,longlong *param_3,undefined8 param_4,
             longlong param_5,longlong param_6,longlong param_7,undefined8 param_8)

{
  longlong *plVar1;
  longlong *plVar2;
  longlong lVar3;
  int *piVar4;
  int iVar5;
  longlong *plVar6;
  undefined8 uVar7;
  longlong lVar8;
  longlong *plVar9;
  longlong lVar10;
  longlong lVar11;
  longlong local_res20;
  
  lVar10 = 0;
  plVar1 = param_3 + param_6;
  if (0 < param_7) {
    lVar8 = param_1 - (longlong)param_2;
    do {
      plVar2 = (longlong *)*plVar1;
      lVar3 = *(longlong *)((longlong)param_2 + lVar8 + 0x18);
      lVar11 = 0;
      plVar6 = plVar2;
      plVar9 = plVar1;
      if (plVar2 == (longlong *)0x0) {
LAB_18000aa77:
        if (lVar11 == 0) goto LAB_18000aa35;
        piVar4 = (int *)*param_2;
        if (*piVar4 + 1 != 0) {
          *piVar4 = *piVar4 + 1;
        }
        *(int **)(param_5 + ((longlong)plVar9 - (longlong)param_3 >> 3) * 8) = piVar4;
      }
      else {
        do {
          if (*plVar6 == lVar3) {
            lVar11 = *plVar9;
            goto LAB_18000aa77;
          }
          plVar6 = (longlong *)plVar9[1];
          plVar9 = plVar9 + 1;
        } while (plVar6 != (longlong *)0x0);
LAB_18000aa35:
        lVar11 = 0;
        local_res20 = 0;
        if (*(code **)(lVar3 + 8) == PyUnicode_Type_exref) {
          uVar7 = FUN_18000a5d0(lVar3,param_3,plVar1,&local_res20,param_8);
          iVar5 = (int)uVar7;
          lVar11 = local_res20;
        }
        else {
          plVar6 = plVar1;
          if ((*(uint *)(*(code **)(lVar3 + 8) + 0xa8) & 0x10000000) == 0) {
            PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() keywords must be strings",
                         param_8);
            iVar5 = -1;
          }
          else {
            while (plVar2 != (longlong *)0x0) {
              iVar5 = PyObject_RichCompareBool(*plVar2,lVar3,2);
              if (iVar5 == 1) {
                iVar5 = 1;
                lVar11 = (longlong)plVar6 - (longlong)param_3 >> 3;
                goto LAB_18000ab4c;
              }
              if (iVar5 == -1) goto LAB_18000abb2;
              plVar2 = (longlong *)plVar6[1];
              plVar6 = plVar6 + 1;
            }
            plVar6 = param_3;
            if (param_3 != plVar1) {
LAB_18000ab20:
              iVar5 = PyObject_RichCompareBool(*(undefined8 *)*plVar6,lVar3,2);
              if (iVar5 == 0) goto code_r0x00018000ab39;
              if (iVar5 == 1) {
                PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                             "%s() got multiple values for keyword argument \'%U\'",param_8,lVar3);
              }
LAB_18000abb2:
              iVar5 = -1;
              goto LAB_18000ab4c;
            }
LAB_18000ab42:
            iVar5 = 0;
          }
        }
LAB_18000ab4c:
        if (iVar5 != 1) {
          if (iVar5 != -1) {
            PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                         "%s() got an unexpected keyword argument \'%U\'",param_8,lVar3);
          }
          return 0xffffffff;
        }
        piVar4 = (int *)*param_2;
        if (*piVar4 + 1 != 0) {
          *piVar4 = *piVar4 + 1;
        }
        *(int **)(param_5 + lVar11 * 8) = piVar4;
      }
      lVar10 = lVar10 + 1;
      param_2 = param_2 + 1;
    } while (lVar10 < param_7);
  }
  return 0;
code_r0x00018000ab39:
  plVar6 = plVar6 + 1;
  if (plVar6 == plVar1) goto LAB_18000ab42;
  goto LAB_18000ab20;
}



// ==== FUN_18000ac00 @ 18000ac00 ====

longlong FUN_18000ac00(longlong param_1,undefined8 *param_2,longlong *param_3,undefined8 param_4,
                      longlong param_5,longlong param_6,longlong param_7,undefined8 param_8)

{
  longlong *plVar1;
  longlong lVar2;
  int iVar3;
  longlong lVar4;
  longlong *plVar5;
  longlong lVar6;
  undefined8 local_res20;
  
  local_res20 = param_4;
  if ((*(uint *)(*(longlong *)(param_1 + 8) + 0xa8) & 0x4000000) != 0) {
    lVar4 = FUN_18000a9c0(param_1,param_2,param_3,param_4,param_5,param_6,param_7,param_8);
    return lVar4;
  }
  lVar4 = 0;
  plVar1 = param_3 + param_6;
  iVar3 = PyArg_ValidateKeywordArguments();
  if (iVar3 == 0) {
    lVar4 = 0xffffffff;
  }
  else {
    lVar2 = *plVar1;
    plVar5 = plVar1;
    lVar6 = lVar4;
    while (lVar2 != 0) {
      if (param_7 <= lVar6) {
        return 0;
      }
      iVar3 = PyDict_GetItemRef(param_1,*(undefined8 *)*plVar5,&local_res20);
      if (iVar3 != 0) {
        if (iVar3 < 0) goto LAB_18000acf1;
        lVar6 = lVar6 + 1;
        *(undefined8 *)(param_5 + ((longlong)plVar5 - (longlong)param_3 >> 3) * 8) = local_res20;
      }
      plVar5 = plVar5 + 1;
      lVar2 = *plVar5;
    }
    if (lVar6 < param_7) {
      FUN_18000a7d0(param_1,param_3,plVar1,param_8);
LAB_18000acf1:
      lVar4 = 0xffffffff;
    }
  }
  return lVar4;
}



// ==== FUN_18000ad30 @ 18000ad30 ====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int * FUN_18000ad30(longlong param_1,int *param_2)

{
  ulonglong uVar1;
  int *piVar2;
  int iVar3;
  ulonglong uVar4;
  
  if (*(code **)(param_1 + 8) != PyLong_Type_exref) {
    if (*(code **)(param_1 + 8) == PyFloat_Type_exref) {
                    /* WARNING: Could not recover jumptable at 0x00018000aded. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      piVar2 = (int *)PyFloat_FromDouble(*(double *)(param_1 + 0x10) + _DAT_180011e00);
      return piVar2;
    }
                    /* WARNING: Could not recover jumptable at 0x00018000adfb. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    piVar2 = (int *)PyNumber_Add(param_1);
    return piVar2;
  }
  uVar1 = *(ulonglong *)(param_1 + 0x10);
  if ((uVar1 & 1) == 0) {
    if (uVar1 >> 3 == 1) {
      iVar3 = -*(int *)(param_1 + 0x18);
      if ((uVar1 & 3) == 0) {
        iVar3 = *(int *)(param_1 + 0x18);
      }
                    /* WARNING: Could not recover jumptable at 0x00018000ad89. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      piVar2 = (int *)PyLong_FromLong(iVar3 + 1);
      return piVar2;
    }
    if (uVar1 >> 3 != 2) {
                    /* WARNING: Could not recover jumptable at 0x00018000ada4. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      piVar2 = (int *)(*(code *)**(undefined8 **)(PyLong_Type_exref + 0x60))
                                (param_1,param_2,(code *)**(undefined8 **)(PyLong_Type_exref + 0x60)
                                );
      return piVar2;
    }
    uVar4 = (ulonglong)*(uint *)(param_1 + 0x1c) << 0x1e | (ulonglong)*(uint *)(param_1 + 0x18);
    if ((uVar1 & 3) != 0) {
      uVar4 = -uVar4;
    }
    param_2 = (int *)PyLong_FromLongLong(uVar4 + 1);
  }
  else if (*param_2 + 1 != 0) {
    *param_2 = *param_2 + 1;
    return param_2;
  }
  return param_2;
}



// ==== FUN_18000ae10 @ 18000ae10 ====

int * FUN_18000ae10(longlong param_1,ulonglong param_2)

{
  code *pcVar1;
  undefined8 *puVar2;
  int iVar3;
  longlong lVar4;
  longlong *plVar5;
  int *piVar6;
  ulonglong uVar7;
  
  pcVar1 = *(code **)(param_1 + 8);
  if (pcVar1 == PyList_Type_exref) {
    uVar7 = param_2;
    if ((longlong)param_2 < 0) {
      uVar7 = *(longlong *)(param_1 + 0x10) + param_2;
    }
    if (uVar7 < *(ulonglong *)(param_1 + 0x10)) {
      piVar6 = *(int **)(*(longlong *)(param_1 + 0x18) + uVar7 * 8);
LAB_18000af65:
      if (*piVar6 + 1 != 0) {
        *piVar6 = *piVar6 + 1;
        return piVar6;
      }
      return piVar6;
    }
  }
  else if (pcVar1 == PyTuple_Type_exref) {
    uVar7 = param_2;
    if ((longlong)param_2 < 0) {
      uVar7 = *(longlong *)(param_1 + 0x10) + param_2;
    }
    if (uVar7 < *(ulonglong *)(param_1 + 0x10)) {
      piVar6 = *(int **)(param_1 + 0x18 + uVar7 * 8);
      goto LAB_18000af65;
    }
  }
  else {
    lVar4 = *(longlong *)(pcVar1 + 0x70);
    puVar2 = *(undefined8 **)(pcVar1 + 0x68);
    if ((lVar4 != 0) && (*(longlong *)(lVar4 + 8) != 0)) {
      plVar5 = (longlong *)PyLong_FromSsize_t(param_2);
      if (plVar5 == (longlong *)0x0) {
        return (int *)0x0;
      }
      piVar6 = (int *)(**(code **)(lVar4 + 8))(param_1,plVar5);
      goto LAB_18000aea1;
    }
    if ((puVar2 != (undefined8 *)0x0) && (puVar2[3] != 0)) {
      if (((longlong)param_2 < 0) && ((code *)*puVar2 != (code *)0x0)) {
        lVar4 = (*(code *)*puVar2)();
        if (-1 < lVar4) {
          piVar6 = (int *)(*(code *)puVar2[3])(param_1,param_2 + lVar4);
          return piVar6;
        }
        iVar3 = PyErr_ExceptionMatches(*(undefined8 *)PyExc_OverflowError_exref);
        if (iVar3 == 0) {
          return (int *)0x0;
        }
        PyErr_Clear();
      }
      piVar6 = (int *)(*(code *)puVar2[3])(param_1,param_2);
      return piVar6;
    }
  }
  plVar5 = (longlong *)PyLong_FromSsize_t(param_2);
  if (plVar5 == (longlong *)0x0) {
    return (int *)0x0;
  }
  piVar6 = (int *)PyObject_GetItem(param_1,plVar5);
LAB_18000aea1:
  if ((-1 < (int)*plVar5) && (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
    _Py_Dealloc(plVar5);
  }
  return piVar6;
}



// ==== FUN_18000af90 @ 18000af90 ====

int * FUN_18000af90(longlong param_1,longlong param_2)

{
  int iVar1;
  int *piVar2;
  longlong *plVar3;
  code *UNRECOVERED_JUMPTABLE;
  longlong lVar4;
  char *pcVar5;
  ulonglong uVar6;
  undefined8 uVar7;
  longlong *local_res8;
  longlong local_20;
  
  lVar4 = *(longlong *)(param_1 + 8);
  if ((*(longlong *)(lVar4 + 0x70) != 0) &&
     (UNRECOVERED_JUMPTABLE = *(code **)(*(longlong *)(lVar4 + 0x70) + 8),
     UNRECOVERED_JUMPTABLE != (code *)0x0)) {
                    /* WARNING: Could not recover jumptable at 0x00018000afc0. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    piVar2 = (int *)(*UNRECOVERED_JUMPTABLE)(param_1);
    return piVar2;
  }
  if ((*(longlong *)(lVar4 + 0x68) == 0) || (*(longlong *)(*(longlong *)(lVar4 + 0x68) + 0x18) == 0)
     ) {
    if (*(int *)(lVar4 + 0xa8) < 0) {
      PyObject_GetOptionalAttr(param_1,DAT_180016950,&local_res8);
      if (local_res8 != (longlong *)0x0) {
        local_20 = param_2;
        piVar2 = (int *)FUN_18000a310((longlong)local_res8,&local_20,0x8000000000000001,0);
        if ((int)*local_res8 < 0) {
          return piVar2;
        }
        *local_res8 = *local_res8 + -1;
        if (*local_res8 != 0) {
          return piVar2;
        }
        _Py_Dealloc(local_res8);
        return piVar2;
      }
      PyErr_Clear();
    }
    pcVar5 = "\'%.200s\' object is not subscriptable";
    uVar7 = *(undefined8 *)(*(longlong *)(param_1 + 8) + 0x18);
    UNRECOVERED_JUMPTABLE = PyExc_TypeError_exref;
LAB_18000b13d:
    PyErr_Format(*(undefined8 *)UNRECOVERED_JUMPTABLE,pcVar5,uVar7);
LAB_18000b146:
    piVar2 = (int *)0x0;
  }
  else {
    if (*(code **)(param_2 + 8) == PyLong_Type_exref) {
      uVar6 = *(ulonglong *)(param_2 + 0x10);
      lVar4 = 1 - (ulonglong)((uint)uVar6 & 3);
      if (uVar6 < 0x10) {
        uVar6 = (ulonglong)*(uint *)(param_2 + 0x18) * lVar4;
      }
      else {
        switch((uVar6 >> 3) * lVar4) {
        case 2:
          uVar6 = (ulonglong)*(uint *)(param_2 + 0x1c) << 0x1e |
                  (ulonglong)*(uint *)(param_2 + 0x18);
          break;
        default:
          uVar6 = PyLong_AsSsize_t(param_2);
          break;
        case 0xfffffffffffffffe:
          uVar6 = -((ulonglong)*(uint *)(param_2 + 0x1c) << 0x1e |
                   (ulonglong)*(uint *)(param_2 + 0x18));
        }
      }
LAB_18000b0a0:
      if (uVar6 == 0xffffffffffffffff) goto LAB_18000b0a6;
    }
    else {
      plVar3 = (longlong *)PyNumber_Index(param_2);
      if (plVar3 != (longlong *)0x0) {
        uVar6 = PyLong_AsSsize_t(plVar3);
        if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
          _Py_Dealloc(plVar3);
        }
        goto LAB_18000b0a0;
      }
      uVar6 = 0xffffffffffffffff;
LAB_18000b0a6:
      lVar4 = PyErr_Occurred();
      if (lVar4 != 0) {
        iVar1 = PyErr_GivenExceptionMatches(lVar4,*(undefined8 *)PyExc_OverflowError_exref);
        if (iVar1 != 0) {
          uVar7 = *(undefined8 *)(*(longlong *)(param_2 + 8) + 0x18);
          PyErr_Clear();
          pcVar5 = "cannot fit \'%.200s\' into an index-sized integer";
          UNRECOVERED_JUMPTABLE = PyExc_IndexError_exref;
          goto LAB_18000b13d;
        }
        goto LAB_18000b146;
      }
    }
    piVar2 = FUN_18000ae10(param_1,uVar6);
  }
  return piVar2;
}



// ==== FUN_18000b1c0 @ 18000b1c0 ====

void FUN_18000b1c0(void)

{
  longlong *plVar1;
  int iVar2;
  longlong lVar3;
  ulonglong uVar4;
  longlong *plVar5;
  longlong *plVar6;
  longlong *plVar7;
  
  lVar3 = PyThreadState_GetUnchecked();
  plVar7 = (longlong *)0x0;
  plVar6 = plVar7;
  if (*(longlong *)(lVar3 + 0x70) != 0) {
    plVar6 = *(longlong **)(*(longlong *)(lVar3 + 0x70) + 8);
  }
  uVar4 = FUN_18000d500((undefined *)plVar6,*(undefined **)PyExc_StopIteration_exref);
  if ((int)uVar4 != 0) {
    plVar6 = *(longlong **)(lVar3 + 0x70);
    *(undefined8 *)(lVar3 + 0x70) = 0;
    plVar5 = plVar7;
    if (plVar6 != (longlong *)0x0) {
      plVar7 = (longlong *)plVar6[1];
      iVar2 = (int)*plVar7 + 1;
      if (iVar2 != 0) {
        *(int *)plVar7 = iVar2;
      }
      plVar5 = (longlong *)PyException_GetTraceback(plVar6);
      if ((plVar5 != (longlong *)0x0) && (iVar2 = (int)*plVar5 + 1, iVar2 != 0)) {
        *(int *)plVar5 = iVar2;
      }
      iVar2 = (int)*plVar7 + 1;
      if (iVar2 != 0) {
        *(int *)plVar7 = iVar2;
      }
      iVar2 = (int)*plVar6 + 1;
      if (iVar2 != 0) {
        *(int *)plVar6 = iVar2;
      }
    }
    plVar1 = (longlong *)**(undefined8 **)(lVar3 + 0x78);
    **(undefined8 **)(lVar3 + 0x78) = plVar6;
    if (((plVar7 != (longlong *)0x0) && (-1 < (int)*plVar7)) &&
       (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
      _Py_Dealloc(plVar7);
    }
    if (((plVar5 != (longlong *)0x0) && (-1 < (int)*plVar5)) &&
       (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
      _Py_Dealloc(plVar5);
    }
    if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) &&
       (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
      _Py_Dealloc(plVar1);
    }
    if (((plVar7 != (longlong *)0x0) && (-1 < (int)*plVar7)) &&
       (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
      _Py_Dealloc(plVar7);
    }
    if (((plVar5 != (longlong *)0x0) && (-1 < (int)*plVar5)) &&
       (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
      _Py_Dealloc(plVar5);
    }
    lVar3 = PyObject_CallFunction
                      (*(undefined8 *)PyExc_RuntimeError_exref,&DAT_180011140,
                       "generator raised StopIteration");
    if (lVar3 == 0) {
      if (((plVar6 != (longlong *)0x0) && (-1 < (int)*plVar6)) &&
         (*plVar6 = *plVar6 + -1, *plVar6 == 0)) {
                    /* WARNING: Could not recover jumptable at 0x00018000b328. Too many branches */
                    /* WARNING: Treating indirect jump as call */
        _Py_Dealloc(plVar6);
        return;
      }
    }
    else {
      PyException_SetCause(lVar3,plVar6);
      PyErr_SetObject(*(undefined8 *)PyExc_RuntimeError_exref,lVar3);
    }
  }
  return;
}



// ==== FUN_18000b360 @ 18000b360 ====

void FUN_18000b360(undefined *param_1,undefined *param_2,undefined *param_3)

{
  undefined *puVar1;
  int iVar2;
  char *pcVar3;
  longlong *plVar4;
  undefined *puVar5;
  longlong *plVar6;
  
  plVar6 = (longlong *)0x0;
  plVar4 = plVar6;
  if ((((code *)param_3 != _Py_NoneStruct_exref) &&
      (plVar4 = (longlong *)param_3, param_3 != (undefined *)0x0)) &&
     (*(code **)(param_3 + 8) != PyTraceBack_Type_exref)) {
                    /* WARNING: Could not recover jumptable at 0x00018000b3e5. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref,"raise: arg 3 must be a traceback or None")
    ;
    return;
  }
  puVar5 = *(undefined **)(param_1 + 8);
  if ((code *)param_2 == _Py_NoneStruct_exref) {
    param_2 = (undefined *)plVar6;
  }
  if ((*(uint *)(puVar5 + 0xa8) >> 0x1e & 1) == 0) {
    if ((-1 < (int)*(uint *)(puVar5 + 0xa8)) || ((*(uint *)(param_1 + 0xa8) & 0x40000000) == 0)) {
      pcVar3 = "raise: exception class must be a subclass of BaseException";
      goto LAB_18000b535;
    }
    if ((longlong *)param_2 == (longlong *)0x0) {
      param_2 = (undefined *)PyTuple_New(0);
LAB_18000b4c4:
      puVar5 = param_1;
      if ((longlong *)param_2 == (longlong *)0x0) {
        return;
      }
    }
    else {
      puVar1 = *(undefined **)((longlong)param_2 + 8);
      puVar5 = param_1;
      if ((*(uint *)(puVar1 + 0xa8) & 0x40000000) != 0) {
        if (puVar1 != param_1) {
          iVar2 = PyObject_IsSubclass(puVar1,param_1);
          if (iVar2 == 0) goto LAB_18000b491;
          puVar5 = puVar1;
          if (iVar2 == -1) {
            return;
          }
        }
        param_1 = param_2;
        if (puVar1 != (undefined *)0x0) goto LAB_18000b3f2;
      }
LAB_18000b491:
      if ((*(uint *)(*(longlong *)((longlong)param_2 + 8) + 0xa8) & 0x4000000) == 0) {
        param_2 = (undefined *)PyTuple_Pack(1,param_2);
        param_1 = puVar5;
        goto LAB_18000b4c4;
      }
      iVar2 = (int)*(longlong *)param_2 + 1;
      if (iVar2 != 0) {
        *(int *)param_2 = iVar2;
      }
    }
    param_1 = (undefined *)PyObject_Call(puVar5,param_2,0);
    if ((-1 < (int)*(longlong *)param_2) &&
       (*(longlong *)param_2 = *(longlong *)param_2 + -1, *(longlong *)param_2 == 0)) {
      _Py_Dealloc(param_2);
    }
    if ((longlong *)param_1 == (longlong *)0x0) {
      return;
    }
    plVar6 = (longlong *)param_1;
    if ((*(uint *)(*(longlong *)((longlong)param_1 + 8) + 0xa8) & 0x40000000) == 0) {
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                   "calling %R should have returned an instance of BaseException, not %R",puVar5);
      goto LAB_18000b418;
    }
  }
  else if ((longlong *)param_2 != (longlong *)0x0) {
    pcVar3 = "instance exception may not have a separate value";
LAB_18000b535:
    PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref,pcVar3);
    return;
  }
LAB_18000b3f2:
  PyErr_SetObject(puVar5,param_1);
  if (plVar4 != (longlong *)0x0) {
    PyException_SetTraceback(param_1,plVar4);
  }
  param_1 = (undefined *)plVar6;
  if (plVar6 == (longlong *)0x0) {
    return;
  }
LAB_18000b418:
  if ((-1 < (int)*(longlong *)param_1) &&
     (*(longlong *)param_1 = *(longlong *)param_1 + -1, *(longlong *)param_1 == 0)) {
    _Py_Dealloc(param_1);
  }
  return;
}



// ==== FUN_18000b560 @ 18000b560 ====

longlong * FUN_18000b560(undefined8 param_1)

{
  undefined8 uVar1;
  longlong *plVar2;
  longlong lVar3;
  longlong *plVar4;
  int iVar5;
  
  uVar1 = DAT_180016730;
  plVar2 = (longlong *)PyImport_GetModule();
  if (plVar2 == (longlong *)0x0) {
    lVar3 = PyErr_Occurred();
    iVar5 = -(uint)(lVar3 != 0);
    plVar2 = (longlong *)0x0;
  }
  else {
    iVar5 = 1;
    lVar3 = PyUnicode_FindChar(param_1,0x2e,0,0x7fffffffffffffff,1);
    if (lVar3 == -1) {
      return plVar2;
    }
    if ((lVar3 == -2) ||
       (plVar4 = (longlong *)PyUnicode_Substring(param_1,0,lVar3), plVar4 == (longlong *)0x0)) {
      if ((int)*plVar2 < 0) {
        return (longlong *)0x0;
      }
      *plVar2 = *plVar2 + -1;
      if (*plVar2 != 0) {
        return (longlong *)0x0;
      }
      _Py_Dealloc(plVar2);
      return (longlong *)0x0;
    }
    if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
      _Py_Dealloc(plVar2);
    }
    plVar2 = (longlong *)PyImport_GetModule(plVar4);
    if (plVar2 == (longlong *)0x0) {
      lVar3 = PyErr_Occurred();
      iVar5 = -(uint)(lVar3 != 0);
    }
    if ((-1 < (int)*plVar4) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)) {
      _Py_Dealloc(plVar4);
    }
  }
  if (iVar5 == 1) {
    return plVar2;
  }
  if (iVar5 == -1) {
    return (longlong *)0x0;
  }
  plVar4 = (longlong *)PyDict_New();
  if (plVar4 == (longlong *)0x0) {
    return plVar2;
  }
  if (plVar2 == (longlong *)0x0) {
    plVar2 = (longlong *)PyImport_ImportModuleLevelObject(param_1,uVar1,plVar4,0,0);
  }
  if (-1 < (int)*plVar4) {
    *plVar4 = *plVar4 + -1;
    if (*plVar4 == 0) {
      _Py_Dealloc(plVar4);
      return plVar2;
    }
    return plVar2;
  }
  return plVar2;
}



// ==== FUN_18000b6b0 @ 18000b6b0 ====

int * FUN_18000b6b0(int *param_1,undefined8 param_2)

{
  int *piVar1;
  ulonglong uVar2;
  ulonglong uVar3;
  uint uVar4;
  
  if (*(code **)(param_1 + 2) != PyLong_Type_exref) {
                    /* WARNING: Could not recover jumptable at 0x00018000b797. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    piVar1 = (int *)PyNumber_Remainder();
    return piVar1;
  }
  uVar3 = *(ulonglong *)(param_1 + 4);
  if ((uVar3 & 1) == 0) {
    if (uVar3 >> 3 == 1) {
      uVar4 = -param_1[6];
      if ((uVar3 & 3) == 0) {
        uVar4 = param_1[6];
      }
      uVar4 = uVar4 & 0x8000001f;
      if ((int)uVar4 < 0) {
        uVar4 = (uVar4 - 1 | 0xffffffe0) + 1;
      }
                    /* WARNING: Could not recover jumptable at 0x00018000b728. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      piVar1 = (int *)PyLong_FromLong((uVar4 >> 0x1f & (uint)(uVar4 != 0)) * 0x20 + uVar4);
      return piVar1;
    }
    if (uVar3 >> 3 != 2) {
                    /* WARNING: Could not recover jumptable at 0x00018000b741. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      piVar1 = (int *)(**(code **)(*(longlong *)(PyLong_Type_exref + 0x60) + 0x18))
                                (param_1,param_2,
                                 *(code **)(*(longlong *)(PyLong_Type_exref + 0x60) + 0x18));
      return piVar1;
    }
    uVar2 = (ulonglong)(uint)param_1[7] << 0x1e | (ulonglong)(uint)param_1[6];
    if ((uVar3 & 3) != 0) {
      uVar2 = -uVar2;
    }
    uVar4 = (uint)((longlong)uVar2 >> 0x3f) & 0x1f;
    uVar3 = (ulonglong)((int)uVar2 + uVar4 & 0x1f) - (ulonglong)uVar4;
    param_1 = (int *)PyLong_FromLongLong((uVar3 >> 0x3f & (ulonglong)(uVar3 != 0)) * 0x20 + uVar3);
  }
  else if (*param_1 + 1 != 0) {
    *param_1 = *param_1 + 1;
    return param_1;
  }
  return param_1;
}



// ==== FUN_18000b7a0 @ 18000b7a0 ====

uint FUN_18000b7a0(longlong param_1,longlong param_2)

{
  uint uVar1;
  code *pcVar2;
  
  if (param_1 == param_2) {
    return 1;
  }
  if (*(code **)(param_1 + 8) == PyLong_Type_exref) {
    return *(uint *)(param_1 + 0x10) & 1;
  }
  if (*(code **)(param_1 + 8) != PyFloat_Type_exref) {
    pcVar2 = (code *)PyObject_RichCompare(param_1,param_2,2);
    if (pcVar2 != (code *)0x0) {
      uVar1 = (uint)(pcVar2 == _Py_TrueStruct_exref);
      if ((pcVar2 != _Py_NoneStruct_exref && pcVar2 != _Py_FalseStruct_exref) && uVar1 == 0) {
        uVar1 = PyObject_IsTrue(pcVar2);
      }
      if ((-1 < *(int *)pcVar2) &&
         (*(longlong *)pcVar2 = *(longlong *)pcVar2 + -1, *(longlong *)pcVar2 == 0)) {
        _Py_Dealloc(pcVar2);
      }
      return uVar1;
    }
    return 0xffffffff;
  }
  if (*(double *)(param_1 + 0x10) != 0.0) {
    return 0;
  }
  return 1;
}



// ==== FUN_18000b890 @ 18000b890 ====

ulonglong FUN_18000b890(longlong param_1)

{
  longlong lVar1;
  longlong lVar2;
  int iVar3;
  uint uVar4;
  ulonglong uVar5;
  longlong lVar6;
  longlong *plVar7;
  
  lVar1 = param_1;
  while( true ) {
    if (lVar1 == 0) {
                    /* WARNING: Could not recover jumptable at 0x00018000b8bc. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      uVar5 = PyType_Ready();
      return uVar5;
    }
    if (*(longlong *)(lVar1 + 0x150) != 0) break;
    lVar1 = *(longlong *)(lVar1 + 0x100);
  }
  lVar1 = *(longlong *)(param_1 + 0x150);
  if (lVar1 != 0) {
    lVar6 = 1;
    if (1 < *(longlong *)(lVar1 + 0x10)) {
      plVar7 = (longlong *)(lVar1 + 0x20);
      do {
        lVar2 = *plVar7;
        if ((*(uint *)(lVar2 + 0xa8) & 0x200) == 0) {
          PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                       "base class \'%.200s\' is not a heap type",*(undefined8 *)(lVar2 + 0x18));
          return 0xffffffff;
        }
        if ((*(longlong *)(param_1 + 0x120) == 0) && (*(longlong *)(lVar2 + 0x120) != 0)) {
          PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,
                       "extension type \'%.200s\' has no __dict__ slot, but base type \'%.200s\' has: either add \'cdef dict __dict__\' to the extension type or add \'__slots__ = [...]\' to the base type"
                       ,*(undefined8 *)(param_1 + 0x18),*(undefined8 *)(lVar2 + 0x18));
          return 0xffffffff;
        }
        lVar6 = lVar6 + 1;
        plVar7 = plVar7 + 1;
      } while (lVar6 < *(longlong *)(lVar1 + 0x10));
    }
  }
  iVar3 = PyGC_Disable();
  *(uint *)(param_1 + 0xa8) = *(uint *)(param_1 + 0xa8) | 0x300;
  uVar4 = PyType_Ready(param_1);
  *(uint *)(param_1 + 0xa8) = *(uint *)(param_1 + 0xa8) & 0xfffffdff;
  if (iVar3 != 0) {
    PyGC_Enable();
  }
  return (ulonglong)uVar4;
}



// ==== FUN_18000b9c0 @ 18000b9c0 ====

undefined8 FUN_18000b9c0(longlong param_1,undefined8 param_2,longlong param_3)

{
  char *pcVar1;
  
  if (*(int *)(*(longlong *)(param_1 + 8) + 0xa8) < 0) {
    if ((param_3 == 0) || (*(longlong *)(param_1 + 0x20) == param_3)) {
      return 0;
    }
    pcVar1 = "Shared Cython type %.200s has the wrong size, try recompiling";
  }
  else {
    pcVar1 = "Shared Cython type %.200s is not a type object";
  }
  PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,pcVar1,param_2);
  return 0xffffffff;
}



// ==== FUN_18000ba20 @ 18000ba20 ====

longlong *
FUN_18000ba20(undefined8 param_1,undefined8 param_2,undefined8 *param_3,undefined8 param_4)

{
  int iVar1;
  char *pcVar2;
  longlong *plVar3;
  longlong *plVar4;
  longlong lVar5;
  undefined8 uVar6;
  longlong *local_res10;
  longlong *local_res18;
  
  local_res10 = (longlong *)0x0;
  pcVar2 = strrchr((char *)*param_3,0x2e);
  if (pcVar2 == (char *)0x0) {
    pcVar2 = (char *)*param_3;
  }
  else {
    pcVar2 = pcVar2 + 1;
  }
  plVar3 = (longlong *)PyUnicode_FromString(pcVar2);
  if (plVar3 == (longlong *)0x0) {
    return (longlong *)0x0;
  }
  plVar4 = (longlong *)PyImport_AddModuleRef("_cython_3_2_4");
  if (plVar4 == (longlong *)0x0) goto LAB_18000bb01;
  lVar5 = PyModule_GetDict(plVar4);
  if (lVar5 != 0) {
    iVar1 = PyDict_GetItemRef(lVar5,plVar3,&local_res10);
    if (iVar1 == 1) {
      uVar6 = FUN_18000b9c0((longlong)local_res10,pcVar2,(longlong)*(int *)(param_3 + 1));
      iVar1 = (int)uVar6;
joined_r0x00018000bba3:
      if (-1 < iVar1) goto LAB_18000bae3;
    }
    else if ((iVar1 != -1) &&
            (local_res10 = (longlong *)PyType_FromMetaclass(param_1,plVar4,param_3,param_4),
            local_res10 != (longlong *)0x0)) {
      PyDict_SetDefaultRef(lVar5,plVar3,local_res10,&local_res18);
      if (local_res18 == local_res10) {
        if ((-1 < (int)*local_res18) && (*local_res18 = *local_res18 + -1, *local_res18 == 0)) {
          _Py_Dealloc(local_res18);
        }
        goto LAB_18000bae3;
      }
      if (local_res18 != (longlong *)0x0) {
        if ((-1 < (int)*local_res10) && (*local_res10 = *local_res10 + -1, *local_res10 == 0)) {
          _Py_Dealloc(local_res10);
        }
        local_res10 = local_res18;
        uVar6 = FUN_18000b9c0((longlong)local_res18,pcVar2,(longlong)*(int *)(param_3 + 1));
        iVar1 = (int)uVar6;
        goto joined_r0x00018000bba3;
      }
    }
    if (((local_res10 != (longlong *)0x0) && (-1 < (int)*local_res10)) &&
       (*local_res10 = *local_res10 + -1, *local_res10 == 0)) {
      _Py_Dealloc(local_res10);
    }
    local_res10 = (longlong *)0x0;
  }
LAB_18000bae3:
  if ((-1 < (int)*plVar4) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)) {
    _Py_Dealloc(plVar4);
  }
LAB_18000bb01:
  if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
    _Py_Dealloc(plVar3);
  }
  return local_res10;
}



// ==== FUN_18000bc30 @ 18000bc30 ====

undefined8
FUN_18000bc30(undefined8 param_1,undefined *param_2,undefined8 *param_3,ulonglong param_4,
             longlong param_5)

{
  longlong lVar1;
  int iVar2;
  undefined8 *_Dst;
  longlong *plVar3;
  undefined8 uVar4;
  undefined8 *puVar5;
  ulonglong uVar6;
  longlong lVar7;
  uint uVar8;
  undefined8 *puVar9;
  int *local_res20;
  int *local_68 [2];
  undefined8 local_58;
  undefined8 local_50;
  longlong local_48;
  
  local_50 = 0;
  lVar1 = *(longlong *)(param_5 + 0x10);
  local_48 = lVar1;
  _Dst = (undefined8 *)PyMem_Malloc((lVar1 + param_4) * 8);
  if (_Dst == (undefined8 *)0x0) {
    PyErr_NoMemory();
    return 0;
  }
  if (param_4 != 0) {
    if (1 < param_4) {
      if ((param_3 + (param_4 - 1) < _Dst) || (_Dst + (param_4 - 1) < param_3)) {
        memcpy(_Dst,param_3,param_4 * 8);
        goto LAB_18000bcf1;
      }
    }
    puVar5 = _Dst;
    uVar6 = param_4;
    do {
      *puVar5 = *(undefined8 *)(((longlong)param_3 - (longlong)_Dst) + (longlong)puVar5);
      puVar5 = puVar5 + 1;
      uVar6 = uVar6 - 1;
    } while (uVar6 != 0);
  }
LAB_18000bcf1:
  plVar3 = (longlong *)PyTuple_New(lVar1);
  if (plVar3 == (longlong *)0x0) {
    PyMem_Free(_Dst);
    return 0;
  }
  uVar8 = 0x10000000;
  puVar5 = _Dst + param_4;
  local_58 = 0;
  puVar9 = puVar5;
  do {
    iVar2 = PyDict_Next(param_5,&local_58,&local_res20,local_68);
    if (iVar2 == 1) {
      if (*local_res20 + 1 != 0) {
        *local_res20 = *local_res20 + 1;
      }
      if (*local_68[0] + 1 != 0) {
        *local_68[0] = *local_68[0] + 1;
      }
    }
    else if (iVar2 == 0) {
      if (uVar8 == 0) {
        PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref,"keywords must be strings");
        uVar4 = local_50;
      }
      else {
        uVar4 = (*(code *)param_2)(param_1,_Dst,param_4,plVar3);
      }
      lVar1 = local_48;
      lVar7 = 0;
      if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
        _Py_Dealloc(plVar3);
      }
      if (0 < lVar1) {
        do {
          plVar3 = (longlong *)puVar5[lVar7];
          if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
            _Py_Dealloc();
          }
          lVar7 = lVar7 + 1;
        } while (lVar7 < lVar1);
      }
      PyMem_Free(_Dst);
      return uVar4;
    }
    uVar8 = uVar8 & *(uint *)(*(longlong *)(local_res20 + 2) + 0xa8);
    *(int **)((longlong)plVar3 + (0x18 - (longlong)puVar5) + (longlong)puVar9) = local_res20;
    *puVar9 = local_68[0];
    puVar9 = puVar9 + 1;
  } while( true );
}



// ==== FUN_18000be70 @ 18000be70 ====

undefined * FUN_18000be70(longlong param_1)

{
  int *piVar1;
  
  piVar1 = *(int **)(param_1 + 0x50);
  if (piVar1 == (int *)0x0) {
    if (*(longlong *)(*(longlong *)(param_1 + 0x10) + 0x18) == 0) {
      if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
        *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
      }
      return _Py_NoneStruct_exref;
    }
    piVar1 = (int *)PyUnicode_FromString();
    *(int **)(param_1 + 0x50) = piVar1;
    if (piVar1 == (int *)0x0) {
      return (undefined *)0x0;
    }
  }
  if (*piVar1 + 1 != 0) {
    *piVar1 = *piVar1 + 1;
  }
  return *(undefined **)(param_1 + 0x50);
}



// ==== FUN_18000bee0 @ 18000bee0 ====

undefined8 FUN_18000bee0(longlong param_1,undefined *param_2)

{
  longlong *plVar1;
  
  if (param_2 == (undefined *)0x0) {
    param_2 = _Py_NoneStruct_exref;
  }
  if (*(int *)param_2 + 1 != 0) {
    *(int *)param_2 = *(int *)param_2 + 1;
  }
  plVar1 = *(longlong **)(param_1 + 0x50);
  *(undefined **)(param_1 + 0x50) = param_2;
  if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) && (*plVar1 = *plVar1 + -1, *plVar1 == 0)
     ) {
    _Py_Dealloc();
  }
  return 0;
}



// ==== FUN_18000bf20 @ 18000bf20 ====

undefined8 FUN_18000bf20(longlong param_1)

{
  int *piVar1;
  
  piVar1 = *(int **)(param_1 + 0x40);
  if (piVar1 == (int *)0x0) {
    piVar1 = (int *)PyUnicode_InternFromString(**(undefined8 **)(param_1 + 0x10));
    *(int **)(param_1 + 0x40) = piVar1;
    if (piVar1 == (int *)0x0) {
      return 0;
    }
  }
  if (*piVar1 + 1 != 0) {
    *piVar1 = *piVar1 + 1;
  }
  return *(undefined8 *)(param_1 + 0x40);
}



// ==== FUN_18000bf70 @ 18000bf70 ====

undefined8 FUN_18000bf70(longlong param_1,int *param_2)

{
  longlong *plVar1;
  
  if ((param_2 != (int *)0x0) && ((*(uint *)(*(longlong *)(param_2 + 2) + 0xa8) & 0x10000000) != 0))
  {
    if (*param_2 + 1 != 0) {
      *param_2 = *param_2 + 1;
    }
    plVar1 = *(longlong **)(param_1 + 0x40);
    *(int **)(param_1 + 0x40) = param_2;
    if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) &&
       (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
      _Py_Dealloc();
    }
    return 0;
  }
  PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref,"__name__ must be set to a string object");
  return 0xffffffff;
}



// ==== FUN_18000c000 @ 18000c000 ====

undefined8 FUN_18000c000(longlong param_1,int *param_2)

{
  longlong *plVar1;
  
  if ((param_2 != (int *)0x0) && ((*(uint *)(*(longlong *)(param_2 + 2) + 0xa8) & 0x10000000) != 0))
  {
    if (*param_2 + 1 != 0) {
      *param_2 = *param_2 + 1;
    }
    plVar1 = *(longlong **)(param_1 + 0x48);
    *(int **)(param_1 + 0x48) = param_2;
    if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) &&
       (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
      _Py_Dealloc();
    }
    return 0;
  }
  PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref,"__qualname__ must be set to a string object"
                 );
  return 0xffffffff;
}



// ==== FUN_18000c0d0 @ 18000c0d0 ====

undefined8 FUN_18000c0d0(longlong param_1)

{
  int *piVar1;
  longlong *plVar2;
  
  plVar2 = (longlong *)(**(code **)(param_1 + 0x90))();
  if (plVar2 == (longlong *)0x0) {
    return 0xffffffff;
  }
  piVar1 = (int *)plVar2[3];
  *(int **)(param_1 + 0x80) = piVar1;
  if (*piVar1 + 1 != 0) {
    *piVar1 = *piVar1 + 1;
  }
  piVar1 = (int *)plVar2[4];
  *(int **)(param_1 + 0x88) = piVar1;
  if (*piVar1 + 1 != 0) {
    *piVar1 = *piVar1 + 1;
  }
  if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
    _Py_Dealloc();
  }
  return 0;
}



// ==== FUN_18000c140 @ 18000c140 ====

undefined8 FUN_18000c140(longlong param_1,undefined *param_2)

{
  longlong *plVar1;
  code *pcVar2;
  
  pcVar2 = _Py_NoneStruct_exref;
  if (((param_2 != (undefined *)0x0) &&
      (pcVar2 = (code *)param_2, (code *)param_2 != _Py_NoneStruct_exref)) &&
     ((*(uint *)(*(longlong *)(param_2 + 8) + 0xa8) & 0x4000000) == 0)) {
    PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref,
                    "__defaults__ must be set to a tuple object");
    return 0xffffffff;
  }
  PyErr_WarnEx(*(undefined8 *)PyExc_RuntimeWarning_exref,
               "changes to cyfunction.__defaults__ will not currently affect the values used in function calls"
               ,1);
  if (*(int *)pcVar2 + 1 != 0) {
    *(int *)pcVar2 = *(int *)pcVar2 + 1;
  }
  plVar1 = *(longlong **)(param_1 + 0x80);
  *(code **)(param_1 + 0x80) = pcVar2;
  if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) && (*plVar1 = *plVar1 + -1, *plVar1 == 0)
     ) {
    _Py_Dealloc();
  }
  return 0;
}



// ==== FUN_18000c200 @ 18000c200 ====

undefined * FUN_18000c200(longlong param_1)

{
  undefined8 uVar1;
  code *pcVar2;
  
  pcVar2 = *(code **)(param_1 + 0x80);
  if ((*(code **)(param_1 + 0x80) == (code *)0x0) &&
     (pcVar2 = _Py_NoneStruct_exref, *(longlong *)(param_1 + 0x90) != 0)) {
    uVar1 = FUN_18000c0d0(param_1);
    if ((int)uVar1 < 0) {
      return (undefined *)0x0;
    }
    pcVar2 = *(code **)(param_1 + 0x80);
  }
  if (*(int *)pcVar2 + 1 != 0) {
    *(int *)pcVar2 = *(int *)pcVar2 + 1;
  }
  return pcVar2;
}



// ==== FUN_18000c250 @ 18000c250 ====

undefined8 FUN_18000c250(longlong param_1,undefined *param_2)

{
  longlong *plVar1;
  code *pcVar2;
  
  pcVar2 = _Py_NoneStruct_exref;
  if (((param_2 != (undefined *)0x0) &&
      (pcVar2 = (code *)param_2, (code *)param_2 != _Py_NoneStruct_exref)) &&
     ((*(uint *)(*(longlong *)(param_2 + 8) + 0xa8) & 0x20000000) == 0)) {
    PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref,
                    "__kwdefaults__ must be set to a dict object");
    return 0xffffffff;
  }
  PyErr_WarnEx(*(undefined8 *)PyExc_RuntimeWarning_exref,
               "changes to cyfunction.__kwdefaults__ will not currently affect the values used in function calls"
               ,1);
  if (*(int *)pcVar2 + 1 != 0) {
    *(int *)pcVar2 = *(int *)pcVar2 + 1;
  }
  plVar1 = *(longlong **)(param_1 + 0x88);
  *(code **)(param_1 + 0x88) = pcVar2;
  if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) && (*plVar1 = *plVar1 + -1, *plVar1 == 0)
     ) {
    _Py_Dealloc();
  }
  return 0;
}



// ==== FUN_18000c310 @ 18000c310 ====

undefined * FUN_18000c310(longlong param_1)

{
  undefined8 uVar1;
  code *pcVar2;
  
  pcVar2 = *(code **)(param_1 + 0x88);
  if ((*(code **)(param_1 + 0x88) == (code *)0x0) &&
     (pcVar2 = _Py_NoneStruct_exref, *(longlong *)(param_1 + 0x90) != 0)) {
    uVar1 = FUN_18000c0d0(param_1);
    if ((int)uVar1 < 0) {
      return (undefined *)0x0;
    }
    pcVar2 = *(code **)(param_1 + 0x88);
  }
  if (*(int *)pcVar2 + 1 != 0) {
    *(int *)pcVar2 = *(int *)pcVar2 + 1;
  }
  return pcVar2;
}



// ==== FUN_18000c360 @ 18000c360 ====

undefined8 FUN_18000c360(longlong param_1,undefined *param_2)

{
  longlong *plVar1;
  
  if ((param_2 == (undefined *)0x0) || ((code *)param_2 == _Py_NoneStruct_exref)) {
    param_2 = (undefined *)0x0;
  }
  else {
    if ((*(uint *)(*(longlong *)(param_2 + 8) + 0xa8) & 0x20000000) == 0) {
      PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref,
                      "__annotations__ must be set to a dict object");
      return 0xffffffff;
    }
    if (*(int *)param_2 + 1 != 0) {
      *(int *)param_2 = *(int *)param_2 + 1;
    }
  }
  plVar1 = *(longlong **)(param_1 + 0x98);
  *(undefined **)(param_1 + 0x98) = param_2;
  if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) && (*plVar1 = *plVar1 + -1, *plVar1 == 0)
     ) {
    _Py_Dealloc();
  }
  return 0;
}



// ==== FUN_18000c3e0 @ 18000c3e0 ====

void FUN_18000c3e0(longlong param_1)

{
  int *piVar1;
  
  piVar1 = *(int **)(param_1 + 0x98);
  if (piVar1 == (int *)0x0) {
    piVar1 = (int *)PyDict_New();
    if (piVar1 == (int *)0x0) {
      return;
    }
    *(int **)(param_1 + 0x98) = piVar1;
  }
  if (*piVar1 + 1 != 0) {
    *piVar1 = *piVar1 + 1;
  }
  return;
}



// ==== FUN_18000c420 @ 18000c420 ====

undefined * FUN_18000c420(longlong param_1)

{
  int *piVar1;
  int *piVar2;
  longlong *plVar3;
  longlong *plVar4;
  code *pcVar5;
  uint uVar6;
  
  piVar2 = DAT_180016a20;
  piVar1 = *(int **)(param_1 + 0xa0);
  if (piVar1 != (int *)0x0) {
    if (*piVar1 + 1 != 0) {
      *piVar1 = *piVar1 + 1;
      return (undefined *)piVar1;
    }
    return (undefined *)piVar1;
  }
  uVar6 = *(uint *)(param_1 + 0x78) & 8;
  if (uVar6 != 0) {
    plVar3 = (longlong *)PyList_New(1);
    if (plVar3 == (longlong *)0x0) {
      return (undefined *)0x0;
    }
    if (*piVar2 + 1 != 0) {
      *piVar2 = *piVar2 + 1;
    }
    *(int **)plVar3[3] = piVar2;
    plVar4 = (longlong *)PyImport_ImportModuleLevelObject(DAT_180016938,0,0,plVar3,0);
    if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
      _Py_Dealloc(plVar3);
    }
    if (plVar4 != (longlong *)0x0) {
      if (*(code **)(plVar4[1] + 0x90) == (code *)0x0) {
        pcVar5 = (code *)PyObject_GetAttr(plVar4,piVar2);
      }
      else {
        pcVar5 = (code *)(**(code **)(plVar4[1] + 0x90))();
      }
      if ((-1 < (int)*plVar4) && (*plVar4 = *plVar4 + -1, *plVar4 == 0)) {
        _Py_Dealloc(plVar4);
      }
      if (pcVar5 != (code *)0x0) goto LAB_18000c511;
    }
    PyErr_Clear();
  }
  pcVar5 = _Py_FalseStruct_exref;
  if (uVar6 != 0) {
    pcVar5 = _Py_TrueStruct_exref;
  }
  if (*(int *)pcVar5 + 1 != 0) {
    *(int *)pcVar5 = *(int *)pcVar5 + 1;
  }
  if (pcVar5 == (code *)0x0) {
    return (undefined *)0x0;
  }
LAB_18000c511:
  if (*(longlong *)(param_1 + 0xa0) == 0) {
    if (*(int *)pcVar5 + 1 != 0) {
      *(int *)pcVar5 = *(int *)pcVar5 + 1;
    }
    *(code **)(param_1 + 0xa0) = pcVar5;
  }
  else {
    if ((-1 < *(int *)pcVar5) &&
       (*(longlong *)pcVar5 = *(longlong *)pcVar5 + -1, *(longlong *)pcVar5 == 0)) {
      _Py_Dealloc(pcVar5);
    }
    pcVar5 = *(code **)(param_1 + 0xa0);
    if (*(int *)pcVar5 + 1 != 0) {
      *(int *)pcVar5 = *(int *)pcVar5 + 1;
    }
  }
  return pcVar5;
}



// ==== FUN_18000c5a0 @ 18000c5a0 ====

undefined8 FUN_18000c5a0(longlong param_1)

{
  longlong *plVar1;
  
  plVar1 = *(longlong **)(param_1 + 0x68);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x68) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x20);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x20) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  PyObject_ClearManagedDict(param_1);
  plVar1 = *(longlong **)(param_1 + 0x40);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x40) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x48);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x48) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x50);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x50) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x58);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x58) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x60);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x60) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x38);
  *(undefined8 *)(param_1 + 0x38) = 0;
  if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) && (*plVar1 = *plVar1 + -1, *plVar1 == 0)
     ) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x80);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x80) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x88);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x88) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x98);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x98) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0xa0);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0xa0) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x70);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x70) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  return 0;
}



// ==== FUN_18000c760 @ 18000c760 ====

void FUN_18000c760(longlong param_1)

{
  PyObject_GC_UnTrack();
  if (*(longlong *)(param_1 + 0x28) != 0) {
    PyObject_ClearWeakRefs(param_1);
  }
  FUN_18000c5a0(param_1);
                    /* WARNING: Could not recover jumptable at 0x00018000c78f. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  PyObject_GC_Del(param_1);
  return;
}



// ==== FUN_18000c7a0 @ 18000c7a0 ====

undefined8 FUN_18000c7a0(longlong param_1,undefined *UNRECOVERED_JUMPTABLE,undefined8 param_3)

{
  undefined8 uVar1;
  
  if ((*(longlong *)(param_1 + 0x68) != 0) &&
     (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x68),param_3),
     (int)uVar1 != 0)) {
    return uVar1;
  }
  if ((*(longlong *)(param_1 + 0x20) != 0) &&
     (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x20),param_3),
     (int)uVar1 != 0)) {
    return uVar1;
  }
  uVar1 = PyObject_VisitManagedDict(param_1,UNRECOVERED_JUMPTABLE,param_3);
  if ((int)uVar1 == 0) {
    if ((*(longlong *)(param_1 + 0x50) != 0) &&
       (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x50),param_3),
       (int)uVar1 != 0)) {
      return uVar1;
    }
    if ((*(longlong *)(param_1 + 0x58) != 0) &&
       (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x58),param_3),
       (int)uVar1 != 0)) {
      return uVar1;
    }
    if ((*(longlong *)(param_1 + 0x38) != 0) &&
       (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x38),param_3),
       (int)uVar1 != 0)) {
      return uVar1;
    }
    if ((*(longlong *)(param_1 + 0x80) != 0) &&
       (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x80),param_3),
       (int)uVar1 != 0)) {
      return uVar1;
    }
    if ((*(longlong *)(param_1 + 0x88) != 0) &&
       (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x88),param_3),
       (int)uVar1 != 0)) {
      return uVar1;
    }
    if ((*(longlong *)(param_1 + 0xa0) != 0) &&
       (uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0xa0),param_3),
       (int)uVar1 != 0)) {
      return uVar1;
    }
    if (*(longlong *)(param_1 + 0x70) != 0) {
                    /* WARNING: Could not recover jumptable at 0x00018000c892. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      uVar1 = (*(code *)UNRECOVERED_JUMPTABLE)(*(longlong *)(param_1 + 0x70),param_3);
      return uVar1;
    }
    uVar1 = 0;
  }
  return uVar1;
}



// ==== FUN_18000c8d0 @ 18000c8d0 ====

undefined8 FUN_18000c8d0(longlong param_1,undefined8 param_2,longlong param_3,longlong param_4)

{
  code *pcVar1;
  longlong lVar2;
  undefined8 uVar3;
  uint uVar4;
  
  pcVar1 = *(code **)(*(longlong *)(param_1 + 0x10) + 8);
  uVar4 = *(uint *)(*(longlong *)(param_1 + 0x10) + 0x10) & 0xf;
  if (uVar4 == 1) {
    if ((param_4 != 0) && (lVar2 = PyDict_Size(param_4), lVar2 != 0)) goto LAB_18000ca04;
  }
  else {
    if (uVar4 == 3) {
      uVar3 = (*pcVar1)(param_2,param_3,param_4);
      return uVar3;
    }
    if (uVar4 == 4) {
      if ((param_4 != 0) && (lVar2 = PyDict_Size(param_4), lVar2 != 0)) goto LAB_18000ca04;
      if (*(longlong *)(param_3 + 0x10) != 0) {
        PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() %s (%zd given)",
                     **(undefined8 **)(param_1 + 0x10),"takes no arguments",
                     *(longlong *)(param_3 + 0x10));
        return 0;
      }
      param_3 = 0;
    }
    else {
      if (uVar4 != 8) {
        PyErr_SetString(*(undefined8 *)PyExc_SystemError_exref,"Bad call flags for CyFunction");
        return 0;
      }
      if ((param_4 != 0) && (lVar2 = PyDict_Size(param_4), lVar2 != 0)) {
LAB_18000ca04:
        PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() %s",
                     **(undefined8 **)(param_1 + 0x10),"takes no keyword arguments");
        return 0;
      }
      if (*(longlong *)(param_3 + 0x10) != 1) {
        PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() %s (%zd given)",
                     **(undefined8 **)(param_1 + 0x10),"takes exactly one argument",
                     *(longlong *)(param_3 + 0x10));
        return 0;
      }
      param_3 = *(longlong *)(param_3 + 0x18);
    }
  }
  uVar3 = (*pcVar1)(param_2,param_3);
  return uVar3;
}



// ==== FUN_18000ca50 @ 18000ca50 ====

undefined8 FUN_18000ca50(longlong param_1,longlong param_2,longlong param_3)

{
  code *UNRECOVERED_JUMPTABLE;
  undefined8 uVar1;
  longlong *plVar2;
  longlong lVar3;
  
  UNRECOVERED_JUMPTABLE = *(code **)(param_1 + 0x30);
  if (UNRECOVERED_JUMPTABLE != (code *)0x0) {
    if ((param_3 != 0) && (*(longlong *)(param_3 + 0x10) != 0)) {
      uVar1 = FUN_18000bc30(param_1,UNRECOVERED_JUMPTABLE,(undefined8 *)(param_2 + 0x18),
                            *(ulonglong *)(param_2 + 0x10),param_3);
      return uVar1;
    }
                    /* WARNING: Could not recover jumptable at 0x00018000caba. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    uVar1 = (*UNRECOVERED_JUMPTABLE)();
    return uVar1;
  }
  if (((byte)*(undefined4 *)(param_1 + 0x78) & 5) == 4) {
    plVar2 = (longlong *)PyTuple_GetSlice(param_2,1,*(undefined8 *)(param_2 + 0x10));
    if (plVar2 != (longlong *)0x0) {
      lVar3 = PyTuple_GetItem(param_2,0);
      if (lVar3 != 0) {
        uVar1 = FUN_18000c8d0(param_1,lVar3,(longlong)plVar2,param_3);
        if ((int)*plVar2 < 0) {
          return uVar1;
        }
        *plVar2 = *plVar2 + -1;
        if (*plVar2 != 0) {
          return uVar1;
        }
        _Py_Dealloc(plVar2);
        return uVar1;
      }
      if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
        _Py_Dealloc(plVar2);
      }
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"unbound method %.200S() needs an argument",
                   *(undefined8 *)(param_1 + 0x48));
    }
    uVar1 = 0;
  }
  else {
    uVar1 = FUN_18000c8d0(param_1,*(undefined8 *)(param_1 + 0x18),param_2,param_3);
  }
  return uVar1;
}



// ==== FUN_18000cb80 @ 18000cb80 ====

undefined8 FUN_18000cb80(longlong param_1,undefined8 *param_2,ulonglong param_3,longlong param_4)

{
  undefined8 *puVar1;
  bool bVar2;
  undefined8 uVar3;
  ulonglong uVar4;
  
  uVar4 = param_3 & 0x7fffffffffffffff;
  puVar1 = *(undefined8 **)(param_1 + 0x10);
  bVar2 = false;
  if (((byte)*(undefined4 *)(param_1 + 0x78) & 5) == 4) {
    if (uVar4 == 0) {
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() %s",*puVar1,"needs an argument");
      return 0;
    }
    bVar2 = true;
  }
  if ((param_4 != 0) && (*(longlong *)(param_4 + 0x10) != 0)) {
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() %s",*puVar1,
                 "takes no keyword arguments");
    return 0;
  }
  if (bVar2) {
    if (!bVar2) {
      return 0;
    }
    uVar3 = *param_2;
    uVar4 = uVar4 - 1;
  }
  else {
    uVar3 = *(undefined8 *)(param_1 + 0x18);
  }
  if (uVar4 != 0) {
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() %s (%zd given)",
                 **(undefined8 **)(param_1 + 0x10),"takes no arguments",uVar4);
    return 0;
  }
                    /* WARNING: Could not recover jumptable at 0x00018000cc73. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  uVar3 = (*(code *)puVar1[1])(uVar3,0);
  return uVar3;
}



// ==== FUN_18000cc80 @ 18000cc80 ====

undefined8 FUN_18000cc80(longlong param_1,undefined8 *param_2,ulonglong param_3,longlong param_4)

{
  undefined8 *puVar1;
  bool bVar2;
  undefined8 uVar3;
  ulonglong uVar4;
  
  uVar4 = param_3 & 0x7fffffffffffffff;
  puVar1 = *(undefined8 **)(param_1 + 0x10);
  bVar2 = false;
  if (((byte)*(undefined4 *)(param_1 + 0x78) & 5) == 4) {
    if (uVar4 == 0) {
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() %s",*puVar1,"needs an argument");
      return 0;
    }
    bVar2 = true;
  }
  if ((param_4 != 0) && (*(longlong *)(param_4 + 0x10) != 0)) {
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() %s",*puVar1,
                 "takes no keyword arguments");
    return 0;
  }
  if (bVar2) {
    if (!bVar2) {
      return 0;
    }
    uVar3 = *param_2;
    param_2 = param_2 + 1;
    uVar4 = uVar4 - 1;
  }
  else {
    uVar3 = *(undefined8 *)(param_1 + 0x18);
  }
  if (uVar4 != 1) {
    PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() %s (%zd given)",
                 **(undefined8 **)(param_1 + 0x10),"takes exactly one argument",uVar4);
    return 0;
  }
                    /* WARNING: Could not recover jumptable at 0x00018000cd79. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  uVar3 = (*(code *)puVar1[1])(uVar3,*param_2);
  return uVar3;
}



// ==== FUN_18000cd80 @ 18000cd80 ====

/* WARNING: Removing unreachable block (ram,0x00018000cdea) */

undefined8 FUN_18000cd80(longlong param_1,undefined8 *param_2,ulonglong param_3)

{
  code *UNRECOVERED_JUMPTABLE_00;
  bool bVar1;
  undefined8 uVar2;
  ulonglong uVar3;
  
  bVar1 = false;
  uVar3 = param_3 & 0x7fffffffffffffff;
  UNRECOVERED_JUMPTABLE_00 = (code *)(*(undefined8 **)(param_1 + 0x10))[1];
  if (((byte)*(undefined4 *)(param_1 + 0x78) & 5) == 4) {
    if (uVar3 == 0) {
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() %s",
                   **(undefined8 **)(param_1 + 0x10),"needs an argument");
      return 0;
    }
    bVar1 = true;
  }
  if (!bVar1) {
                    /* WARNING: Could not recover jumptable at 0x00018000ce19. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    uVar2 = (*UNRECOVERED_JUMPTABLE_00)(*(undefined8 *)(param_1 + 0x18),param_2,uVar3);
    return uVar2;
  }
                    /* WARNING: Could not recover jumptable at 0x00018000ce07. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  uVar2 = (*UNRECOVERED_JUMPTABLE_00)(*param_2,param_2 + 1,uVar3 - 1);
  return uVar2;
}



// ==== FUN_18000ce20 @ 18000ce20 ====

undefined8 FUN_18000ce20(longlong param_1,undefined8 *param_2,ulonglong param_3,undefined8 param_4)

{
  bool bVar1;
  undefined8 uVar2;
  ulonglong uVar3;
  
  uVar3 = param_3 & 0x7fffffffffffffff;
  bVar1 = false;
  if (((byte)*(undefined4 *)(param_1 + 0x78) & 5) == 4) {
    if (uVar3 == 0) {
      PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"%.200s() %s",
                   **(undefined8 **)(param_1 + 0x10),"needs an argument");
      return 0;
    }
    bVar1 = true;
  }
  if (bVar1) {
    if (!bVar1) {
      return 0;
    }
    uVar2 = *param_2;
    param_2 = param_2 + 1;
    uVar3 = uVar3 - 1;
  }
  else {
    uVar2 = *(undefined8 *)(param_1 + 0x18);
  }
  uVar2 = (*(code *)(*(undefined8 **)(param_1 + 0x10))[1])
                    (uVar2,*(undefined8 *)(param_1 + 0x38),param_2,uVar3,param_4);
  return uVar2;
}



// ==== FUN_18000ced0 @ 18000ced0 ====

undefined *
FUN_18000ced0(longlong param_1,undefined8 param_2,int *param_3,undefined8 param_4,int *param_5,
             int *param_6,int *param_7)

{
  code *pcVar1;
  uint uVar2;
  code *pcVar3;
  
  pcVar1 = (code *)_PyObject_GC_New(DAT_180016d90);
  pcVar3 = (code *)0x0;
  if (pcVar1 != (code *)0x0) {
    *(undefined4 *)(pcVar1 + 0x78) = 0;
    *(longlong *)(pcVar1 + 0x28) = 0;
    *(longlong *)(pcVar1 + 0x10) = param_1;
    *(code **)(pcVar1 + 0x18) = pcVar1;
    *(longlong *)(pcVar1 + 0x68) = 0;
    if ((param_5 != (int *)0x0) && (*param_5 + 1 != 0)) {
      *param_5 = *param_5 + 1;
    }
    *(int **)(pcVar1 + 0x20) = param_5;
    *(longlong *)(pcVar1 + 0x40) = 0;
    if (*param_3 + 1 != 0) {
      *param_3 = *param_3 + 1;
    }
    *(int **)(pcVar1 + 0x48) = param_3;
    *(longlong *)(pcVar1 + 0x50) = 0;
    *(longlong *)(pcVar1 + 0x38) = 0;
    *(int **)(pcVar1 + 0x58) = param_6;
    if (*param_6 + 1 != 0) {
      *param_6 = *param_6 + 1;
    }
    if ((param_7 != (int *)0x0) && (*param_7 + 1 != 0)) {
      *param_7 = *param_7 + 1;
    }
    *(int **)(pcVar1 + 0x60) = param_7;
    *(longlong *)(pcVar1 + 0x70) = 0;
    *(longlong *)(pcVar1 + 0x80) = 0;
    *(longlong *)(pcVar1 + 0x88) = 0;
    *(longlong *)(pcVar1 + 0x90) = 0;
    *(longlong *)(pcVar1 + 0x98) = 0;
    *(longlong *)(pcVar1 + 0xa0) = 0;
    uVar2 = *(uint *)(param_1 + 0x10) & 0x28f;
    if (uVar2 != 3) {
      if (uVar2 == 4) {
        pcVar3 = FUN_18000cb80;
      }
      else if (uVar2 == 8) {
        pcVar3 = FUN_18000cc80;
      }
      else if (uVar2 == 0x82) {
        pcVar3 = FUN_18000cd80;
      }
      else {
        if (uVar2 != 0x282) {
          PyErr_SetString(*(undefined8 *)PyExc_SystemError_exref,"Bad call flags for CyFunction");
          if (*(int *)pcVar1 < 0) {
            return (undefined *)0x0;
          }
          *(longlong *)pcVar1 = *(longlong *)pcVar1 + -1;
          if (*(longlong *)pcVar1 != 0) {
            return (undefined *)0x0;
          }
          _Py_Dealloc(pcVar1);
          return (undefined *)0x0;
        }
        pcVar3 = FUN_18000ce20;
      }
    }
    *(code **)(pcVar1 + 0x30) = pcVar3;
    PyObject_GC_Track(pcVar1);
    pcVar3 = pcVar1;
  }
  return pcVar3;
}



// ==== FUN_18000d040 @ 18000d040 ====

int FUN_18000d040(longlong param_1,int param_2,int param_3)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  
  iVar4 = 0;
  iVar5 = param_2 + -1;
  iVar3 = 0;
  if ((-1 < iVar5) && (*(int *)(param_1 + 8 + (longlong)iVar5 * 0x10) < param_3)) {
    return param_2;
  }
  if (0 < iVar5) {
    do {
      iVar3 = iVar5 - iVar4;
      if (iVar3 < 0) {
        iVar3 = iVar3 + 1;
      }
      iVar3 = (iVar3 >> 1) + iVar4;
      iVar1 = *(int *)(param_1 + 8 + (longlong)iVar3 * 0x10);
      iVar2 = iVar3;
      if (iVar1 <= param_3) {
        if (param_3 <= iVar1) {
          return iVar3;
        }
        iVar4 = iVar3 + 1;
        iVar2 = iVar5;
      }
      iVar5 = iVar2;
    } while (iVar4 < iVar5);
  }
  iVar4 = iVar3 + 1;
  if (param_3 <= *(int *)(param_1 + 8 + (longlong)iVar3 * 0x10)) {
    iVar4 = iVar3;
  }
  return iVar4;
}



// ==== FUN_18000d0d0 @ 18000d0d0 ====

void FUN_18000d0d0(int *param_1,int param_2,int *param_3)

{
  longlong *plVar1;
  int iVar2;
  undefined8 *puVar3;
  longlong lVar4;
  longlong lVar5;
  longlong lVar6;
  int iVar7;
  
  if (param_2 != 0) {
    lVar4 = *(longlong *)(param_1 + 2);
    if (lVar4 == 0) {
      puVar3 = (undefined8 *)PyMem_Malloc(0x400);
      if (puVar3 != (undefined8 *)0x0) {
        *(undefined8 **)(param_1 + 2) = puVar3;
        param_1[1] = 0x40;
        *param_1 = 1;
        *(int *)(puVar3 + 1) = param_2;
        *puVar3 = param_3;
        if (*param_3 + 1 != 0) {
          *param_3 = *param_3 + 1;
          return;
        }
      }
    }
    else {
      iVar7 = *param_1;
      iVar2 = FUN_18000d040(lVar4,iVar7,param_2);
      lVar6 = (longlong)iVar2;
      if ((iVar2 < iVar7) &&
         (puVar3 = (undefined8 *)(lVar4 + lVar6 * 0x10),
         *(int *)(lVar4 + 8 + lVar6 * 0x10) == param_2)) {
        plVar1 = (longlong *)*puVar3;
        *puVar3 = param_3;
        if (*param_3 + 1 != 0) {
          *param_3 = *param_3 + 1;
        }
        if ((-1 < (int)*plVar1) && (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
          _Py_Dealloc();
        }
      }
      else {
        if (iVar7 == param_1[1]) {
          iVar7 = param_1[1] + 0x40;
          lVar4 = PyMem_Realloc(lVar4,(longlong)iVar7 << 4);
          if (lVar4 == 0) {
            return;
          }
          *(longlong *)(param_1 + 2) = lVar4;
          param_1[1] = iVar7;
        }
        lVar5 = (longlong)*param_1;
        if (lVar6 < lVar5) {
          puVar3 = (undefined8 *)(lVar5 * 0x10 + lVar4);
          do {
            lVar5 = lVar5 + -1;
            *puVar3 = puVar3[-2];
            puVar3[1] = puVar3[-1];
            puVar3 = puVar3 + -2;
          } while (lVar6 < lVar5);
        }
        *(int *)(lVar4 + 8 + lVar6 * 0x10) = param_2;
        *(int **)(lVar4 + lVar6 * 0x10) = param_3;
        *param_1 = *param_1 + 1;
        if (*param_3 + 1 != 0) {
          *param_3 = *param_3 + 1;
        }
      }
    }
  }
  return;
}



// ==== FUN_18000d220 @ 18000d220 ====

void FUN_18000d220(undefined8 param_1,undefined8 param_2,int param_3,undefined8 param_4)

{
  longlong lVar1;
  longlong *plVar2;
  longlong *plVar3;
  int iVar4;
  longlong lVar5;
  longlong *plVar6;
  longlong *plVar7;
  int iVar8;
  longlong *plVar9;
  
  lVar5 = PyThreadState_GetUnchecked();
  lVar1 = DAT_180016da0;
  if ((((param_3 == 0) || (DAT_180016da0 == 0)) ||
      (iVar8 = (int)DAT_180016d98, iVar4 = FUN_18000d040(DAT_180016da0,iVar8,param_3),
      iVar8 <= iVar4)) || (*(int *)(lVar1 + 8 + (longlong)iVar4 * 0x10) != param_3)) {
LAB_18000d299:
    plVar2 = *(longlong **)(lVar5 + 0x70);
    plVar7 = (longlong *)0x0;
    *(undefined8 *)(lVar5 + 0x70) = 0;
    plVar9 = plVar7;
    if (plVar2 != (longlong *)0x0) {
      plVar9 = (longlong *)plVar2[1];
      iVar4 = (int)*plVar9 + 1;
      if (iVar4 != 0) {
        *(int *)plVar9 = iVar4;
      }
      plVar7 = (longlong *)plVar2[5];
      if ((plVar7 != (longlong *)0x0) && (iVar4 = (int)*plVar7 + 1, iVar4 != 0)) {
        *(int *)plVar7 = iVar4;
      }
    }
    plVar6 = (longlong *)PyCode_NewEmpty(param_4,param_1,param_3);
    if (plVar6 != (longlong *)0x0) {
      if ((plVar2 != (longlong *)0x0) && ((longlong *)plVar2[5] != plVar7)) {
        PyException_SetTraceback(plVar2,plVar7);
      }
      plVar3 = *(longlong **)(lVar5 + 0x70);
      *(longlong **)(lVar5 + 0x70) = plVar2;
      if (((plVar3 != (longlong *)0x0) && (-1 < (int)*plVar3)) &&
         (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
        _Py_Dealloc();
      }
      if (((plVar9 != (longlong *)0x0) && (-1 < (int)*plVar9)) &&
         (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
        _Py_Dealloc(plVar9);
      }
      if (((plVar7 != (longlong *)0x0) && (-1 < (int)*plVar7)) &&
         (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
        _Py_Dealloc(plVar7);
      }
      FUN_18000d0d0((int *)&DAT_180016d98,param_3,(int *)plVar6);
      goto LAB_18000d394;
    }
    if (((plVar9 != (longlong *)0x0) && (-1 < (int)*plVar9)) &&
       (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
      _Py_Dealloc(plVar9);
    }
    if ((plVar2 != (longlong *)0x0) && (-1 < (int)*plVar2)) {
      *plVar2 = *plVar2 + -1;
      lVar1 = *plVar2;
      plVar6 = plVar2;
      goto joined_r0x00018000d30e;
    }
  }
  else {
    plVar6 = *(longlong **)(lVar1 + (longlong)iVar4 * 0x10);
    iVar4 = (int)*plVar6 + 1;
    if (iVar4 != 0) {
      *(int *)plVar6 = iVar4;
    }
    if (plVar6 == (longlong *)0x0) goto LAB_18000d299;
LAB_18000d394:
    plVar7 = (longlong *)PyFrame_New(lVar5,plVar6,DAT_180016730,0);
    if (plVar7 != (longlong *)0x0) {
      *(int *)(plVar7 + 5) = param_3;
      PyTraceBack_Here(plVar7);
      if (plVar6 == (longlong *)0x0) goto LAB_18000d3dd;
    }
    if (-1 < (int)*plVar6) {
      *plVar6 = *plVar6 + -1;
      lVar1 = *plVar6;
joined_r0x00018000d30e:
      if (lVar1 == 0) {
        _Py_Dealloc(plVar6);
      }
    }
  }
  if (plVar7 == (longlong *)0x0) {
    return;
  }
LAB_18000d3dd:
  if ((-1 < (int)*plVar7) && (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
    _Py_Dealloc(plVar7);
  }
  return;
}



// ==== FUN_18000d410 @ 18000d410 ====

bool FUN_18000d410(undefined *param_1,undefined *param_2)

{
  longlong lVar1;
  longlong lVar2;
  longlong *plVar3;
  
  if (param_1 != param_2) {
    lVar1 = *(longlong *)(param_1 + 0x158);
    if (lVar1 != 0) {
      lVar2 = 0;
      if (0 < *(longlong *)(lVar1 + 0x10)) {
        plVar3 = (longlong *)(lVar1 + 0x18);
        do {
          if ((undefined *)*plVar3 == param_2) {
            return true;
          }
          lVar2 = lVar2 + 1;
          plVar3 = plVar3 + 1;
        } while (lVar2 < *(longlong *)(lVar1 + 0x10));
      }
      return false;
    }
    while (param_1 = *(undefined **)(param_1 + 0x100), param_1 != param_2) {
      if (param_1 == (undefined *)0x0) {
        return (code *)param_2 == PyBaseObject_Type_exref;
      }
    }
  }
  return true;
}



// ==== FUN_18000d470 @ 18000d470 ====

undefined8 FUN_18000d470(undefined *param_1,undefined *param_2,undefined *param_3)

{
  longlong lVar1;
  longlong lVar2;
  undefined *puVar3;
  longlong *plVar4;
  
  if ((param_1 != param_2) && (param_1 != param_3)) {
    lVar1 = *(longlong *)(param_1 + 0x158);
    puVar3 = param_1;
    if (lVar1 != 0) {
      lVar2 = 0;
      if (0 < *(longlong *)(lVar1 + 0x10)) {
        plVar4 = (longlong *)(lVar1 + 0x18);
        do {
          if ((undefined *)*plVar4 == param_2) {
            return 1;
          }
          if ((undefined *)*plVar4 == param_3) {
            return 1;
          }
          lVar2 = lVar2 + 1;
          plVar4 = plVar4 + 1;
        } while (lVar2 < *(longlong *)(lVar1 + 0x10));
      }
      return 0;
    }
    do {
      puVar3 = *(undefined **)(puVar3 + 0x100);
      if (puVar3 == param_2) {
        return 1;
      }
    } while (puVar3 != (undefined *)0x0);
    if ((code *)param_2 != PyBaseObject_Type_exref) {
      do {
        param_1 = *(undefined **)(param_1 + 0x100);
        if (param_1 == param_3) {
          return 1;
        }
      } while (param_1 != (undefined *)0x0);
      if ((code *)param_3 != PyBaseObject_Type_exref) {
        return 0;
      }
    }
  }
  return 1;
}



// ==== FUN_18000d500 @ 18000d500 ====

ulonglong FUN_18000d500(undefined *param_1,undefined *param_2)

{
  longlong lVar1;
  code *pcVar2;
  longlong *plVar3;
  longlong *plVar4;
  code *pcVar5;
  ulonglong uVar6;
  longlong lVar7;
  longlong lVar8;
  longlong lVar9;
  longlong lVar10;
  
  if (param_1 == param_2) {
    return 1;
  }
  if ((*(int *)(*(longlong *)(param_1 + 8) + 0xa8) < 0) &&
     ((*(uint *)(param_1 + 0xa8) & 0x40000000) != 0)) {
    if (((int)*(uint *)(*(longlong *)(param_2 + 8) + 0xa8) < 0) &&
       ((*(uint *)(param_2 + 0xa8) & 0x40000000) != 0)) {
      lVar1 = *(longlong *)(param_1 + 0x158);
      if (lVar1 == 0) {
        while (param_1 = *(undefined **)(param_1 + 0x100), param_1 != param_2) {
          if (param_1 == (undefined *)0x0) {
            return (ulonglong)((code *)param_2 == PyBaseObject_Type_exref);
          }
        }
      }
      else {
        lVar7 = 0;
        if (*(longlong *)(lVar1 + 0x10) < 1) {
          return 0;
        }
        plVar3 = (longlong *)(lVar1 + 0x18);
        while ((undefined *)*plVar3 != param_2) {
          lVar7 = lVar7 + 1;
          plVar3 = plVar3 + 1;
          if (*(longlong *)(lVar1 + 0x10) <= lVar7) {
            return 0;
          }
        }
      }
      return 1;
    }
    if ((*(uint *)(*(longlong *)(param_2 + 8) + 0xa8) >> 0x1a & 1) != 0) {
      lVar7 = 0;
      lVar1 = *(longlong *)(param_2 + 0x10);
      if (lVar1 < 1) {
        return 0;
      }
      plVar3 = (longlong *)(param_2 + 0x18);
      plVar4 = plVar3;
      lVar8 = lVar7;
      do {
        if (param_1 == (undefined *)*plVar4) {
          return 1;
        }
        lVar8 = lVar8 + 1;
        plVar4 = plVar4 + 1;
        lVar10 = lVar7;
      } while (lVar8 < lVar1);
      do {
        pcVar2 = (code *)*plVar3;
        if ((*(int *)(*(longlong *)(pcVar2 + 8) + 0xa8) < 0) &&
           ((*(uint *)(pcVar2 + 0xa8) & 0x40000000) != 0)) {
          if ((code *)param_1 == pcVar2) {
            return 1;
          }
          lVar8 = *(longlong *)(param_1 + 0x158);
          pcVar5 = (code *)param_1;
          if (lVar8 == 0) {
            do {
              pcVar5 = *(code **)(pcVar5 + 0x100);
              if (pcVar5 == pcVar2) {
                return 1;
              }
            } while (pcVar5 != (code *)0x0);
            if (pcVar2 == PyBaseObject_Type_exref) {
              return 1;
            }
          }
          else if (0 < *(longlong *)(lVar8 + 0x10)) {
            plVar4 = (longlong *)(lVar8 + 0x18);
            lVar9 = lVar7;
            do {
              if ((code *)*plVar4 == pcVar2) {
                return 1;
              }
              lVar9 = lVar9 + 1;
              plVar4 = plVar4 + 1;
            } while (lVar9 < *(longlong *)(lVar8 + 0x10));
          }
        }
        lVar10 = lVar10 + 1;
        plVar3 = plVar3 + 1;
        if (lVar1 <= lVar10) {
          return 0;
        }
      } while( true );
    }
  }
                    /* WARNING: Could not recover jumptable at 0x00018000d6c9. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  uVar6 = PyErr_GivenExceptionMatches();
  return uVar6;
}



// ==== FUN_18000d6d0 @ 18000d6d0 ====

undefined8 FUN_18000d6d0(longlong param_1,longlong *param_2)

{
  code *pcVar1;
  longlong *plVar2;
  bool bVar3;
  int iVar4;
  undefined7 extraout_var;
  ulonglong uVar5;
  undefined8 uVar6;
  code *pcVar7;
  code *pcVar8;
  longlong *plVar9;
  code *local_res8 [2];
  longlong *local_res18;
  code *local_res20;
  
  local_res8[0] = *(code **)(param_1 + 0x70);
  *(undefined8 *)(param_1 + 0x70) = 0;
  local_res20 = (code *)0x0;
  local_res18 = (longlong *)0x0;
  if (local_res8[0] == (code *)0x0) {
LAB_18000d985:
    if (((local_res18 != (longlong *)0x0) && (-1 < (int)*local_res18)) &&
       (*local_res18 = *local_res18 + -1, *local_res18 == 0)) {
      _Py_Dealloc(local_res18);
    }
    if (((local_res8[0] != (code *)0x0) && (-1 < *(int *)local_res8[0])) &&
       (*(longlong *)local_res8[0] = *(longlong *)local_res8[0] + -1,
       *(longlong *)local_res8[0] == 0)) {
      _Py_Dealloc(local_res8[0]);
    }
    if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
      *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
    }
    *param_2 = (longlong)_Py_NoneStruct_exref;
    return 0;
  }
  local_res20 = *(code **)(local_res8[0] + 8);
  if (*(int *)local_res20 + 1 != 0) {
    *(int *)local_res20 = *(int *)local_res20 + 1;
  }
  plVar9 = *(longlong **)(local_res8[0] + 0x28);
  if ((plVar9 != (longlong *)0x0) && (iVar4 = (int)*plVar9 + 1, iVar4 != 0)) {
    *(int *)plVar9 = iVar4;
  }
  local_res18 = plVar9;
  if (local_res20 == (code *)0x0) goto LAB_18000d985;
  pcVar7 = *(code **)PyExc_StopIteration_exref;
  if (local_res20 == pcVar7) {
    pcVar8 = _Py_NoneStruct_exref;
    if (local_res8[0] == (code *)0x0) {
      if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
        *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
        pcVar8 = _Py_NoneStruct_exref;
      }
    }
    else {
      pcVar1 = *(code **)(local_res8[0] + 8);
      if (pcVar1 == pcVar7) {
        pcVar8 = *(code **)(local_res8[0] + 0x48);
        if (*(int *)pcVar8 + 1 != 0) {
          *(int *)pcVar8 = *(int *)pcVar8 + 1;
        }
        if ((-1 < *(int *)local_res8[0]) &&
           (*(longlong *)local_res8[0] = *(longlong *)local_res8[0] + -1,
           *(longlong *)local_res8[0] == 0)) {
          _Py_Dealloc(local_res8[0]);
          plVar9 = local_res18;
        }
      }
      else if ((*(uint *)(pcVar1 + 0xa8) & 0x4000000) == 0) {
        pcVar8 = local_res8[0];
        bVar3 = FUN_18000d410(pcVar1,pcVar7);
        if ((int)CONCAT71(extraout_var,bVar3) != 0) goto LAB_18000d863;
      }
      else {
        if (*(longlong *)(local_res8[0] + 0x10) < 1) {
          if (*(int *)_Py_NoneStruct_exref + 1 != 0) {
            *(int *)_Py_NoneStruct_exref = *(int *)_Py_NoneStruct_exref + 1;
            pcVar8 = _Py_NoneStruct_exref;
          }
        }
        else {
          pcVar8 = *(code **)(local_res8[0] + 0x18);
          if (*(int *)pcVar8 + 1 != 0) {
            *(int *)pcVar8 = *(int *)pcVar8 + 1;
          }
        }
        if ((-1 < *(int *)local_res8[0]) &&
           (*(longlong *)local_res8[0] = *(longlong *)local_res8[0] + -1,
           *(longlong *)local_res8[0] == 0)) {
          _Py_Dealloc(local_res8[0]);
          plVar9 = local_res18;
        }
      }
    }
    if (pcVar8 == (code *)0x0) {
LAB_18000d863:
      PyErr_NormalizeException(&local_res20,local_res8,&local_res18);
      if ((*(longlong *)(local_res8[0] + 8) != *(longlong *)PyExc_StopIteration_exref) &&
         (iVar4 = PyType_IsSubtype(), iVar4 == 0)) goto LAB_18000d89e;
      if (((local_res18 != (longlong *)0x0) && (-1 < (int)*local_res18)) &&
         (*local_res18 = *local_res18 + -1, *local_res18 == 0)) {
        _Py_Dealloc();
      }
      if ((-1 < *(int *)local_res20) &&
         (*(longlong *)local_res20 = *(longlong *)local_res20 + -1, *(longlong *)local_res20 == 0))
      {
        _Py_Dealloc();
      }
      pcVar8 = *(code **)(local_res8[0] + 0x48);
      pcVar7 = local_res8[0];
      if (*(int *)pcVar8 + 1 != 0) {
        *(int *)pcVar8 = *(int *)pcVar8 + 1;
      }
    }
    else {
      pcVar7 = local_res20;
      if (((plVar9 != (longlong *)0x0) && (-1 < (int)*plVar9)) &&
         (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
        _Py_Dealloc(plVar9);
        pcVar7 = local_res20;
      }
    }
    if ((-1 < *(int *)pcVar7) &&
       (*(longlong *)pcVar7 = *(longlong *)pcVar7 + -1, *(longlong *)pcVar7 == 0)) {
      _Py_Dealloc();
    }
    *param_2 = (longlong)pcVar8;
    uVar6 = 0;
  }
  else {
    uVar5 = FUN_18000d500(local_res20,pcVar7);
    if ((int)uVar5 != 0) goto LAB_18000d863;
LAB_18000d89e:
    pcVar8 = local_res20;
    plVar9 = local_res18;
    pcVar7 = local_res8[0];
    if ((local_res8[0] != (code *)0x0) && (*(longlong **)(local_res8[0] + 0x28) != local_res18)) {
      PyException_SetTraceback(local_res8[0],local_res18);
    }
    plVar2 = *(longlong **)(param_1 + 0x70);
    *(code **)(param_1 + 0x70) = pcVar7;
    if (((plVar2 != (longlong *)0x0) && (-1 < (int)*plVar2)) &&
       (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
      _Py_Dealloc();
    }
    if (((pcVar8 != (code *)0x0) && (-1 < *(int *)pcVar8)) &&
       (*(longlong *)pcVar8 = *(longlong *)pcVar8 + -1, *(longlong *)pcVar8 == 0)) {
      _Py_Dealloc(pcVar8);
    }
    if (((plVar9 != (longlong *)0x0) && (-1 < (int)*plVar9)) &&
       (*plVar9 = *plVar9 + -1, *plVar9 == 0)) {
      _Py_Dealloc(plVar9);
    }
    uVar6 = 0xffffffff;
  }
  return uVar6;
}



// ==== FUN_18000d9f0 @ 18000d9f0 ====

int FUN_18000d9f0(longlong param_1,longlong param_2,longlong *param_3)

{
  longlong *plVar1;
  longlong lVar2;
  undefined8 uVar3;
  longlong lVar4;
  longlong *plVar5;
  
  if (*(int *)(param_1 + 0x70) == -1) {
    if (param_2 != 0) {
      PyErr_SetNone(*(undefined8 *)PyExc_StopIteration_exref);
    }
    return -1;
  }
  lVar2 = PyThreadState_GetUnchecked();
  if ((*(longlong *)(param_1 + 0x20) != 0) &&
     (lVar4 = *(longlong *)(*(longlong *)(param_1 + 0x20) + 0x28), lVar4 != 0)) {
    lVar4 = *(longlong *)(lVar4 + 0x18);
    uVar3 = PyThreadState_GetFrame(lVar2);
    *(undefined8 *)(lVar4 + 0x10) = uVar3;
  }
  *(undefined8 *)(param_1 + 0x28) = *(undefined8 *)(lVar2 + 0x78);
  *(longlong **)(lVar2 + 0x78) = (longlong *)(param_1 + 0x20);
  lVar4 = (**(code **)(param_1 + 0x10))(param_1,lVar2,param_2);
  *(undefined8 *)(lVar2 + 0x78) = *(undefined8 *)(param_1 + 0x28);
  *(undefined8 *)(param_1 + 0x28) = 0;
  if (*(longlong *)(param_1 + 0x20) != 0) {
    plVar5 = (longlong *)PyException_GetTraceback();
    if (plVar5 != (longlong *)0x0) {
      plVar1 = *(longlong **)(plVar5[3] + 0x10);
      if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(plVar5[3] + 0x10) = 0, -1 < (int)*plVar1)
          ) && (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
        _Py_Dealloc();
      }
      if ((-1 < (int)*plVar5) && (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
        _Py_Dealloc(plVar5);
      }
    }
  }
  *param_3 = lVar4;
  if (*(int *)(param_1 + 0x70) == -1) {
    return (lVar4 != 0) - 1;
  }
  return 1;
}



// ==== FUN_18000db20 @ 18000db20 ====

undefined8 FUN_18000db20(undefined8 param_1,int param_2,undefined *param_3,int param_4)

{
  longlong *plVar1;
  longlong *plVar2;
  longlong *plVar3;
  longlong lVar4;
  int iVar5;
  
  if (param_2 != 0) {
    return 0;
  }
  if ((code *)param_3 == _Py_NoneStruct_exref) {
    if (param_4 == 0) {
      PyErr_SetNone(*(undefined8 *)PyExc_StopIteration_exref);
    }
  }
  else {
    plVar1 = *(longlong **)PyExc_StopIteration_exref;
    plVar2 = (longlong *)PyTuple_New(1);
    if (plVar2 != (longlong *)0x0) {
      if (*(int *)param_3 + 1 != 0) {
        *(int *)param_3 = *(int *)param_3 + 1;
      }
      plVar2[3] = (longlong)param_3;
      plVar3 = (longlong *)PyObject_Call(plVar1,plVar2,0);
      if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
        _Py_Dealloc(plVar2);
      }
      if (plVar3 != (longlong *)0x0) {
        lVar4 = PyThreadState_GetUnchecked();
        if (**(longlong **)(lVar4 + 0x78) == 0) {
          iVar5 = (int)*plVar1 + 1;
          if (iVar5 != 0) {
            *(int *)plVar1 = iVar5;
          }
          if (plVar3[5] != 0) {
            PyException_SetTraceback(plVar3,0);
          }
          plVar2 = *(longlong **)(lVar4 + 0x70);
          *(longlong **)(lVar4 + 0x70) = plVar3;
          if (((plVar2 != (longlong *)0x0) && (-1 < (int)*plVar2)) &&
             (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
            _Py_Dealloc();
          }
          if ((plVar1 == (longlong *)0x0) || ((int)*plVar1 < 0)) goto LAB_18000dc3e;
          *plVar1 = *plVar1 + -1;
          lVar4 = *plVar1;
        }
        else {
          PyErr_SetObject(plVar1,plVar3);
          if ((int)*plVar3 < 0) goto LAB_18000dc3e;
          *plVar3 = *plVar3 + -1;
          lVar4 = *plVar3;
          plVar1 = plVar3;
        }
        if (lVar4 == 0) {
          _Py_Dealloc(plVar1);
        }
      }
      goto LAB_18000dc3e;
    }
  }
  if (param_3 == (undefined *)0x0) {
    return 0;
  }
LAB_18000dc3e:
  if ((-1 < *(int *)param_3) &&
     (*(longlong *)param_3 = *(longlong *)param_3 + -1, *(longlong *)param_3 == 0)) {
    _Py_Dealloc(param_3);
  }
  return 0;
}



// ==== FUN_18000dc90 @ 18000dc90 ====

int FUN_18000dc90(longlong param_1,longlong *param_2)

{
  longlong *plVar1;
  int iVar2;
  longlong lVar3;
  longlong *local_res8;
  
  *(undefined8 *)(param_1 + 0x40) = 0;
  plVar1 = *(longlong **)(param_1 + 0x38);
  local_res8 = (longlong *)0x0;
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x38) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  lVar3 = PyThreadState_GetUnchecked();
  FUN_18000d6d0(lVar3,(longlong *)&local_res8);
  plVar1 = local_res8;
  iVar2 = FUN_18000d9f0(param_1,(longlong)local_res8,param_2);
  if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) && (*plVar1 = *plVar1 + -1, *plVar1 == 0)
     ) {
    _Py_Dealloc(plVar1);
  }
  return iVar2;
}



// ==== FUN_18000dd20 @ 18000dd20 ====

int FUN_18000dd20(longlong param_1,undefined *param_2,undefined8 param_3,longlong *param_4)

{
  longlong *plVar1;
  int iVar2;
  longlong *local_res8 [2];
  
  local_res8[0] = (longlong *)0x0;
  iVar2 = (*(code *)param_2)(*(undefined8 *)(param_1 + 0x38),param_3,local_res8);
  if (iVar2 == 1) {
    *param_4 = (longlong)local_res8[0];
    return 1;
  }
  *(undefined8 *)(param_1 + 0x40) = 0;
  plVar1 = *(longlong **)(param_1 + 0x38);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x38) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  iVar2 = FUN_18000d9f0(param_1,(longlong)local_res8[0],param_4);
  if (((local_res8[0] != (longlong *)0x0) && (-1 < (int)*local_res8[0])) &&
     (*local_res8[0] = *local_res8[0] + -1, *local_res8[0] == 0)) {
    _Py_Dealloc();
  }
  return iVar2;
}



// ==== FUN_18000ddd0 @ 18000ddd0 ====

undefined * FUN_18000ddd0(longlong param_1,undefined *param_2)

{
  char cVar1;
  longlong lVar2;
  int iVar3;
  undefined *puVar4;
  longlong lVar5;
  undefined *local_res8;
  longlong local_18;
  undefined *local_10;
  
  cVar1 = *(char *)(param_1 + 0x74);
  local_res8 = (undefined *)0x0;
  *(undefined1 *)(param_1 + 0x74) = 1;
  if (cVar1 == '\0') {
    lVar5 = param_1;
    if (*(undefined **)(param_1 + 0x40) == (undefined *)0x0) {
      lVar2 = *(longlong *)(param_1 + 0x38);
      if (lVar2 == 0) {
        iVar3 = FUN_18000d9f0(param_1,(longlong)param_2,(longlong *)&local_res8);
      }
      else {
        if (((code *)param_2 == _Py_NoneStruct_exref) && (iVar3 = PyIter_Check(lVar2), iVar3 != 0))
        {
          puVar4 = (undefined *)(**(code **)(*(longlong *)(lVar2 + 8) + 0xe0))(lVar2);
        }
        else {
          local_18 = lVar2;
          local_10 = param_2;
          puVar4 = (undefined *)
                   PyObject_VectorcallMethod(DAT_180016b08,&local_18,0x8000000000000002);
        }
        if (puVar4 != (undefined *)0x0) {
          *(undefined1 *)(param_1 + 0x74) = 0;
          return puVar4;
        }
        iVar3 = FUN_18000dc90(param_1,(longlong *)&local_res8);
      }
    }
    else {
      iVar3 = FUN_18000dd20(param_1,*(undefined **)(param_1 + 0x40),param_2,(longlong *)&local_res8)
      ;
    }
    *(undefined1 *)(param_1 + 0x74) = 0;
    puVar4 = local_res8;
    if (iVar3 == 1) {
      return local_res8;
    }
  }
  else {
    lVar5 = *(longlong *)PyExc_ValueError_exref;
    PyErr_SetString(lVar5,"generator already executing");
    iVar3 = -1;
    puVar4 = (undefined *)0x0;
  }
  puVar4 = (undefined *)FUN_18000db20(lVar5,iVar3,puVar4,0);
  return puVar4;
}



// ==== FUN_18000df10 @ 18000df10 ====

int FUN_18000df10(longlong param_1,undefined *param_2,longlong *param_3)

{
  char cVar1;
  int iVar2;
  longlong lVar3;
  longlong local_18;
  undefined *local_10;
  
  cVar1 = *(char *)(param_1 + 0x74);
  *(undefined1 *)(param_1 + 0x74) = 1;
  if (cVar1 != '\0') {
    PyErr_SetString(*(undefined8 *)PyExc_ValueError_exref,"generator already executing");
    *param_3 = 0;
    return -1;
  }
  if (*(undefined **)(param_1 + 0x40) == (undefined *)0x0) {
    lVar3 = *(longlong *)(param_1 + 0x38);
    if (lVar3 == 0) {
      iVar2 = FUN_18000d9f0(param_1,(longlong)param_2,param_3);
    }
    else {
      if (((code *)param_2 == _Py_NoneStruct_exref) && (iVar2 = PyIter_Check(lVar3), iVar2 != 0)) {
        lVar3 = (**(code **)(*(longlong *)(lVar3 + 8) + 0xe0))(lVar3);
      }
      else {
        local_18 = lVar3;
        local_10 = param_2;
        lVar3 = PyObject_VectorcallMethod(DAT_180016b08,&local_18,0x8000000000000002,0);
      }
      if (lVar3 != 0) {
        *(undefined1 *)(param_1 + 0x74) = 0;
        *param_3 = lVar3;
        return 1;
      }
      iVar2 = FUN_18000dc90(param_1,param_3);
    }
  }
  else {
    iVar2 = FUN_18000dd20(param_1,*(undefined **)(param_1 + 0x40),param_2,param_3);
  }
  *(undefined1 *)(param_1 + 0x74) = 0;
  return iVar2;
}



// ==== FUN_18000e020 @ 18000e020 ====

int FUN_18000e020(undefined8 param_1,longlong param_2)

{
  undefined8 uVar1;
  longlong lVar2;
  int iVar3;
  longlong *local_res8;
  longlong *local_res10 [2];
  undefined8 uStack_20;
  
  iVar3 = 0;
  local_res8 = (longlong *)0x0;
  if (*(longlong *)(param_2 + 8) == DAT_180016da8) {
    uVar1 = FUN_18000e250(param_2,(longlong *)&local_res8);
    iVar3 = (int)uVar1;
  }
  else {
    PyObject_GetOptionalAttr(param_2,DAT_180016960,local_res10);
    if (local_res10[0] == (longlong *)0x0) {
      lVar2 = PyErr_Occurred();
      if (lVar2 != 0) {
        PyErr_WriteUnraisable(param_2);
      }
    }
    else {
      uStack_20 = 0;
      local_res8 = (longlong *)
                   FUN_18000a310((longlong)local_res10[0],&uStack_20,0x8000000000000000,0);
      if ((-1 < (int)*local_res10[0]) &&
         (*local_res10[0] = *local_res10[0] + -1, *local_res10[0] == 0)) {
        _Py_Dealloc(local_res10[0]);
      }
      iVar3 = 0;
      if (local_res8 == (longlong *)0x0) {
        iVar3 = -1;
      }
    }
  }
  if (((local_res8 != (longlong *)0x0) && (-1 < (int)*local_res8)) &&
     (*local_res8 = *local_res8 + -1, *local_res8 == 0)) {
    _Py_Dealloc(local_res8);
  }
  return (iVar3 != -1) - 1;
}



// ==== FUN_18000e120 @ 18000e120 ====

undefined * FUN_18000e120(longlong param_1)

{
  char cVar1;
  longlong lVar2;
  int iVar3;
  undefined *puVar4;
  longlong lVar5;
  undefined *local_res8 [4];
  
  cVar1 = *(char *)(param_1 + 0x74);
  local_res8[0] = (undefined *)0x0;
  *(undefined1 *)(param_1 + 0x74) = 1;
  if (cVar1 != '\0') {
    PyErr_SetString(*(undefined8 *)PyExc_ValueError_exref,"generator already executing");
    return (undefined *)0x0;
  }
  lVar5 = param_1;
  if (*(undefined **)(param_1 + 0x40) == (undefined *)0x0) {
    lVar2 = *(longlong *)(param_1 + 0x38);
    if (lVar2 == 0) {
      iVar3 = FUN_18000d9f0(param_1,(longlong)_Py_NoneStruct_exref,(longlong *)local_res8);
    }
    else {
      if (*(longlong *)(lVar2 + 8) == DAT_180016da8) {
        puVar4 = FUN_18000e120(lVar2);
      }
      else {
        puVar4 = (undefined *)(**(code **)(*(longlong *)(lVar2 + 8) + 0xe0))();
      }
      if (puVar4 != (undefined *)0x0) {
        *(undefined1 *)(param_1 + 0x74) = 0;
        return puVar4;
      }
      iVar3 = FUN_18000dc90(param_1,(longlong *)local_res8);
    }
  }
  else {
    iVar3 = FUN_18000dd20(param_1,*(undefined **)(param_1 + 0x40),_Py_NoneStruct_exref,
                          (longlong *)local_res8);
  }
  *(undefined1 *)(param_1 + 0x74) = 0;
  if (iVar3 == 1) {
    return local_res8[0];
  }
  puVar4 = (undefined *)FUN_18000db20(lVar5,iVar3,local_res8[0],1);
  return puVar4;
}



// ==== FUN_18000e200 @ 18000e200 ====

undefined * FUN_18000e200(longlong param_1)

{
  undefined8 uVar1;
  longlong *local_res18 [2];
  
  local_res18[0] = (longlong *)0x0;
  uVar1 = FUN_18000e250(param_1,(longlong *)local_res18);
  if ((int)uVar1 == -1) {
    return (undefined *)0x0;
  }
  if (((local_res18[0] != (longlong *)0x0) && (-1 < (int)*local_res18[0])) &&
     (*local_res18[0] = *local_res18[0] + -1, *local_res18[0] == 0)) {
    _Py_Dealloc();
  }
  return _Py_NoneStruct_exref;
}



// ==== FUN_18000e250 @ 18000e250 ====

undefined8 FUN_18000e250(longlong param_1,longlong *param_2)

{
  char cVar1;
  longlong *plVar2;
  longlong *plVar3;
  code *pcVar4;
  code *pcVar5;
  longlong lVar6;
  int iVar7;
  uint uVar8;
  longlong lVar9;
  undefined8 uVar10;
  undefined8 *puVar11;
  longlong lVar12;
  code *pcVar13;
  
  cVar1 = *(char *)(param_1 + 0x74);
  *(undefined1 *)(param_1 + 0x74) = 1;
  if (cVar1 != '\0') {
    PyErr_SetString(*(undefined8 *)PyExc_ValueError_exref,"generator already executing");
    *param_2 = 0;
    return 0xffffffff;
  }
  lVar12 = 0;
  uVar8 = 0;
  plVar2 = *(longlong **)(param_1 + 0x38);
  if (plVar2 == (longlong *)0x0) {
LAB_18000e2f5:
    PyErr_SetNone(*(undefined8 *)PyExc_GeneratorExit_exref);
  }
  else {
    iVar7 = (int)*plVar2 + 1;
    if (iVar7 != 0) {
      *(int *)plVar2 = iVar7;
    }
    iVar7 = FUN_18000e020(param_1,(longlong)plVar2);
    *(undefined8 *)(param_1 + 0x40) = 0;
    plVar3 = *(longlong **)(param_1 + 0x38);
    if (((plVar3 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x38) = 0, -1 < (int)*plVar3)) &&
       (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
      _Py_Dealloc();
    }
    if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
      _Py_Dealloc(plVar2);
    }
    if (iVar7 == 0) goto LAB_18000e2f5;
  }
  iVar7 = FUN_18000d9f0(param_1,0,param_2);
  if (iVar7 == -1) {
    lVar9 = PyThreadState_GetUnchecked();
    *(undefined1 *)(param_1 + 0x74) = 0;
    if (*(longlong *)(lVar9 + 0x70) != 0) {
      pcVar13 = *(code **)(*(longlong *)(lVar9 + 0x70) + 8);
      pcVar4 = *(code **)PyExc_StopIteration_exref;
      pcVar5 = *(code **)PyExc_GeneratorExit_exref;
      if ((pcVar13 != pcVar5) && (pcVar13 != pcVar4)) {
        if ((*(int *)(*(longlong *)(pcVar13 + 8) + 0xa8) < 0) &&
           ((*(uint *)(pcVar13 + 0xa8) & 0x40000000) != 0)) {
          if (pcVar5 == (code *)0x0) {
            lVar6 = *(longlong *)(pcVar13 + 0x158);
            if (lVar6 == 0) {
              do {
                pcVar13 = *(code **)(pcVar13 + 0x100);
                if (pcVar13 == pcVar4) goto LAB_18000e3df;
              } while (pcVar13 != (code *)0x0);
              uVar8 = (uint)(pcVar4 == PyBaseObject_Type_exref);
            }
            else if (0 < *(longlong *)(lVar6 + 0x10)) {
              puVar11 = (undefined8 *)(lVar6 + 0x18);
              do {
                if ((code *)*puVar11 == pcVar4) goto LAB_18000e3df;
                lVar12 = lVar12 + 1;
                puVar11 = puVar11 + 1;
              } while (lVar12 < *(longlong *)(lVar6 + 0x10));
            }
          }
          else {
            uVar10 = FUN_18000d470(pcVar13,pcVar5,pcVar4);
            uVar8 = (uint)uVar10;
          }
        }
        else {
          iVar7 = PyErr_GivenExceptionMatches(pcVar13);
          if (iVar7 != 0) goto LAB_18000e403;
          uVar8 = PyErr_GivenExceptionMatches(pcVar13,pcVar4);
        }
LAB_18000e3ff:
        if (uVar8 == 0) goto LAB_18000e46d;
      }
LAB_18000e403:
      plVar2 = *(longlong **)(lVar9 + 0x70);
      *(undefined8 *)(lVar9 + 0x70) = 0;
      if (((plVar2 != (longlong *)0x0) && (-1 < (int)*plVar2)) &&
         (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
        _Py_Dealloc();
      }
    }
    uVar10 = 0;
  }
  else {
    if ((iVar7 == 0) && ((code *)*param_2 == _Py_NoneStruct_exref)) {
      *(undefined1 *)(param_1 + 0x74) = 0;
      return 0;
    }
    plVar2 = (longlong *)*param_2;
    if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
      _Py_Dealloc();
    }
    pcVar13 = PyExc_RuntimeError_exref;
    *param_2 = 0;
    PyErr_SetString(*(undefined8 *)pcVar13,"generator ignored GeneratorExit");
    *(undefined1 *)(param_1 + 0x74) = 0;
LAB_18000e46d:
    uVar10 = 0xffffffff;
  }
  return uVar10;
LAB_18000e3df:
  uVar8 = 1;
  goto LAB_18000e3ff;
}



// ==== FUN_18000e490 @ 18000e490 ====

/* WARNING: Function: __security_check_cookie replaced with injection: security_check_cookie */

undefined *
FUN_18000e490(longlong param_1,undefined *param_2,undefined *param_3,undefined *param_4,
             longlong param_5)

{
  char cVar1;
  longlong *plVar2;
  int iVar3;
  ulonglong uVar4;
  undefined *puVar5;
  longlong lVar6;
  longlong lVar7;
  undefined1 auStackY_b8 [32];
  undefined *local_88;
  longlong *local_80;
  undefined8 local_70;
  undefined *local_68;
  undefined *local_60;
  undefined *local_58;
  ulonglong local_50;
  
  local_50 = DAT_180015000 ^ (ulonglong)auStackY_b8;
  cVar1 = *(char *)(param_1 + 0x74);
  *(undefined1 *)(param_1 + 0x74) = 1;
  if (cVar1 != '\0') {
    PyErr_SetString(*(undefined8 *)PyExc_ValueError_exref,"generator already executing");
    return (undefined *)0x0;
  }
  plVar2 = *(longlong **)(param_1 + 0x38);
  lVar7 = param_1;
  if (plVar2 == (longlong *)0x0) {
LAB_18000e570:
    FUN_18000b360(param_2,param_3,param_4);
  }
  else {
    iVar3 = (int)*plVar2 + 1;
    if (iVar3 != 0) {
      *(int *)plVar2 = iVar3;
    }
    puVar5 = param_2;
    uVar4 = FUN_18000d500(param_2,*(undefined **)PyExc_GeneratorExit_exref);
    if ((int)uVar4 == 0) {
      if (plVar2[1] == DAT_180016da8) {
        puVar5 = FUN_18000e490((longlong)plVar2,param_2,param_3,param_4,param_5);
        local_88 = puVar5;
      }
      else {
        PyObject_GetOptionalAttr(plVar2,DAT_180016b48);
        if (local_80 == (longlong *)0x0) {
          if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
            _Py_Dealloc(plVar2);
          }
          lVar6 = PyErr_Occurred();
          if (lVar6 != 0) {
            *(undefined1 *)(param_1 + 0x74) = 0;
            return (undefined *)0x0;
          }
          *(undefined8 *)(param_1 + 0x40) = 0;
          plVar2 = *(longlong **)(param_1 + 0x38);
          if (((plVar2 != (longlong *)0x0) &&
              (*(undefined8 *)(param_1 + 0x38) = 0, -1 < (int)*plVar2)) &&
             (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
            _Py_Dealloc();
          }
          goto LAB_18000e570;
        }
        if (param_5 == 0) {
          local_70 = 0;
          local_68 = param_2;
          local_60 = param_3;
          local_58 = param_4;
          puVar5 = (undefined *)FUN_18000a310((longlong)local_80,&local_68,0x8000000000000003,0);
        }
        else {
          puVar5 = (undefined *)FUN_18000a1d0((longlong)local_80,param_5,0);
        }
        local_88 = puVar5;
        if ((-1 < (int)*local_80) && (*local_80 = *local_80 + -1, *local_80 == 0)) {
          _Py_Dealloc(local_80);
        }
      }
      if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
        _Py_Dealloc(plVar2);
      }
      if (puVar5 != (undefined *)0x0) {
        *(undefined1 *)(param_1 + 0x74) = 0;
        return puVar5;
      }
      iVar3 = FUN_18000dc90(param_1,(longlong *)&local_88);
      goto LAB_18000e592;
    }
    iVar3 = FUN_18000e020(puVar5,(longlong)plVar2);
    if ((-1 < (int)*plVar2) && (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
      _Py_Dealloc(plVar2);
    }
    *(undefined8 *)(param_1 + 0x40) = 0;
    plVar2 = *(longlong **)(param_1 + 0x38);
    if (((plVar2 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x38) = 0, -1 < (int)*plVar2)) &&
       (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
      _Py_Dealloc();
    }
    if (-1 < iVar3) goto LAB_18000e570;
  }
  local_88 = (undefined *)0x0;
  iVar3 = FUN_18000d9f0(param_1,0,(longlong *)&local_88);
LAB_18000e592:
  *(undefined1 *)(param_1 + 0x74) = 0;
  if (iVar3 != 1) {
    local_88 = (undefined *)FUN_18000db20(lVar7,iVar3,local_88,0);
  }
  return local_88;
}



// ==== FUN_18000e730 @ 18000e730 ====

undefined * FUN_18000e730(longlong param_1,longlong param_2)

{
  int iVar1;
  undefined *puVar2;
  undefined *local_res18;
  undefined *local_res20;
  undefined *local_18 [2];
  
  local_res20 = (undefined *)0x0;
  local_res18 = (undefined *)0x0;
  iVar1 = PyArg_UnpackTuple(param_2,"throw",1,3,local_18,&local_res20,&local_res18);
  if (iVar1 == 0) {
    return (undefined *)0x0;
  }
  puVar2 = FUN_18000e490(param_1,local_18[0],local_res20,local_res18,param_2);
  return puVar2;
}



// ==== FUN_18000e7c0 @ 18000e7c0 ====

undefined8 FUN_18000e7c0(longlong param_1,undefined *param_2,undefined8 param_3)

{
  undefined8 uVar1;
  
  if ((*(longlong *)(param_1 + 0x18) != 0) &&
     (uVar1 = (*(code *)param_2)(*(longlong *)(param_1 + 0x18),param_3), (int)uVar1 != 0)) {
    return uVar1;
  }
  if ((*(longlong *)(param_1 + 0x30) != 0) &&
     (uVar1 = (*(code *)param_2)(*(longlong *)(param_1 + 0x30),param_3), (int)uVar1 != 0)) {
    return uVar1;
  }
  if ((*(longlong *)(param_1 + 0x38) != 0) &&
     (uVar1 = (*(code *)param_2)(*(longlong *)(param_1 + 0x38),param_3), (int)uVar1 != 0)) {
    return uVar1;
  }
  if ((*(longlong *)(param_1 + 0x20) != 0) &&
     (uVar1 = (*(code *)param_2)(*(longlong *)(param_1 + 0x20),param_3), (int)uVar1 != 0)) {
    return uVar1;
  }
  return 0;
}



// ==== FUN_18000e840 @ 18000e840 ====

undefined8 FUN_18000e840(longlong param_1)

{
  longlong *plVar1;
  
  plVar1 = *(longlong **)(param_1 + 0x18);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x18) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x30);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x30) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  *(undefined8 *)(param_1 + 0x40) = 0;
  plVar1 = *(longlong **)(param_1 + 0x38);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x38) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x20);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x20) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x60);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x60) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x68);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x68) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x48);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x48) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x50);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x50) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  plVar1 = *(longlong **)(param_1 + 0x58);
  if (((plVar1 != (longlong *)0x0) && (*(undefined8 *)(param_1 + 0x58) = 0, -1 < (int)*plVar1)) &&
     (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
    _Py_Dealloc();
  }
  return 0;
}



// ==== FUN_18000e970 @ 18000e970 ====

void FUN_18000e970(longlong param_1)

{
  int iVar1;
  
  PyObject_GC_UnTrack();
  PyObject_ClearWeakRefs(param_1);
  if (-1 < *(int *)(param_1 + 0x70)) {
    PyObject_GC_Track(param_1);
    iVar1 = PyObject_CallFinalizerFromDealloc(param_1);
    if (iVar1 != 0) {
      return;
    }
    PyObject_GC_UnTrack(param_1);
  }
  FUN_18000e840(param_1);
                    /* WARNING: Could not recover jumptable at 0x00018000e9bd. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  PyObject_GC_Del(param_1);
  return;
}



// ==== FUN_18000e9d0 @ 18000e9d0 ====

void FUN_18000e9d0(longlong param_1)

{
  longlong lVar1;
  longlong *plVar2;
  longlong lVar3;
  undefined8 uVar4;
  int iVar5;
  longlong *plVar6;
  longlong *plVar7;
  longlong *local_res8;
  
  if (-1 < *(int *)(param_1 + 0x70)) {
    lVar3 = PyThreadState_GetUnchecked();
    plVar6 = (longlong *)0x0;
    lVar1 = *(longlong *)(lVar3 + 0x70);
    *(undefined8 *)(lVar3 + 0x70) = 0;
    plVar7 = plVar6;
    if (lVar1 != 0) {
      plVar7 = *(longlong **)(lVar1 + 8);
      iVar5 = (int)*plVar7 + 1;
      if (iVar5 != 0) {
        *(int *)plVar7 = iVar5;
      }
      plVar6 = *(longlong **)(lVar1 + 0x28);
      if ((plVar6 != (longlong *)0x0) && (iVar5 = (int)*plVar6 + 1, iVar5 != 0)) {
        *(int *)plVar6 = iVar5;
      }
    }
    if ((*(int *)(param_1 + 0x70) != 0) || (lVar1 != 0)) {
      local_res8 = (longlong *)0x0;
      uVar4 = FUN_18000e250(param_1,(longlong *)&local_res8);
      if ((int)uVar4 == -1) {
        PyErr_WriteUnraisable(param_1);
      }
      else if (((local_res8 != (longlong *)0x0) && (-1 < (int)*local_res8)) &&
              (*local_res8 = *local_res8 + -1, *local_res8 == 0)) {
        _Py_Dealloc();
      }
      if ((lVar1 != 0) && (*(longlong **)(lVar1 + 0x28) != plVar6)) {
        PyException_SetTraceback(lVar1,plVar6);
      }
    }
    plVar2 = *(longlong **)(lVar3 + 0x70);
    *(longlong *)(lVar3 + 0x70) = lVar1;
    if (((plVar2 != (longlong *)0x0) && (-1 < (int)*plVar2)) &&
       (*plVar2 = *plVar2 + -1, *plVar2 == 0)) {
      _Py_Dealloc();
    }
    if (((plVar7 != (longlong *)0x0) && (-1 < (int)*plVar7)) &&
       (*plVar7 = *plVar7 + -1, *plVar7 == 0)) {
      _Py_Dealloc(plVar7);
    }
    if (((plVar6 != (longlong *)0x0) && (-1 < (int)*plVar6)) &&
       (*plVar6 = *plVar6 + -1, *plVar6 == 0)) {
      _Py_Dealloc(plVar6);
    }
  }
  return;
}



// ==== FUN_18000eb20 @ 18000eb20 ====

undefined8 FUN_18000eb20(longlong param_1,int *param_2)

{
  longlong *plVar1;
  
  if ((param_2 != (int *)0x0) && ((*(uint *)(*(longlong *)(param_2 + 2) + 0xa8) & 0x10000000) != 0))
  {
    if (*param_2 + 1 != 0) {
      *param_2 = *param_2 + 1;
    }
    plVar1 = *(longlong **)(param_1 + 0x48);
    *(int **)(param_1 + 0x48) = param_2;
    if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) &&
       (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
      _Py_Dealloc();
    }
    return 0;
  }
  PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref,"__name__ must be set to a string object");
  return 0xffffffff;
}



// ==== FUN_18000ebb0 @ 18000ebb0 ====

undefined8 FUN_18000ebb0(longlong param_1,int *param_2)

{
  longlong *plVar1;
  
  if ((param_2 != (int *)0x0) && ((*(uint *)(*(longlong *)(param_2 + 2) + 0xa8) & 0x10000000) != 0))
  {
    if (*param_2 + 1 != 0) {
      *param_2 = *param_2 + 1;
    }
    plVar1 = *(longlong **)(param_1 + 0x50);
    *(int **)(param_1 + 0x50) = param_2;
    if (((plVar1 != (longlong *)0x0) && (-1 < (int)*plVar1)) &&
       (*plVar1 = *plVar1 + -1, *plVar1 == 0)) {
      _Py_Dealloc();
    }
    return 0;
  }
  PyErr_SetString(*(undefined8 *)PyExc_TypeError_exref,"__qualname__ must be set to a string object"
                 );
  return 0xffffffff;
}



// ==== FUN_18000ec20 @ 18000ec20 ====

undefined * FUN_18000ec20(longlong param_1)

{
  int *piVar1;
  undefined8 uVar2;
  longlong *plVar3;
  undefined8 uVar4;
  longlong *plVar5;
  int iVar6;
  
  piVar1 = *(int **)(param_1 + 0x68);
  if (piVar1 != (int *)0x0) {
    if (*piVar1 + 1 == 0) {
      return (undefined *)piVar1;
    }
    *piVar1 = *piVar1 + 1;
    return (undefined *)piVar1;
  }
  if (*(longlong *)(param_1 + 0x60) != 0) {
    plVar3 = (longlong *)PyDict_New();
    if (plVar3 != (longlong *)0x0) {
      uVar2 = *(undefined8 *)(param_1 + 0x60);
      uVar4 = PyThreadState_Get();
      plVar5 = (longlong *)PyFrame_New(uVar4,uVar2,plVar3,0);
      if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
        _Py_Dealloc(plVar3);
      }
      if (plVar5 != (longlong *)0x0) {
        if (*(longlong *)(param_1 + 0x68) == 0) {
          *(longlong **)(param_1 + 0x68) = plVar5;
        }
        else {
          if ((-1 < (int)*plVar5) && (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
            _Py_Dealloc(plVar5);
          }
          plVar5 = *(longlong **)(param_1 + 0x68);
        }
        iVar6 = (int)*plVar5 + 1;
        if (iVar6 == 0) {
          return (undefined *)plVar5;
        }
        *(int *)plVar5 = iVar6;
        return (undefined *)plVar5;
      }
    }
    return (undefined *)0x0;
  }
  return _Py_NoneStruct_exref;
}



// ==== FUN_18000ed30 @ 18000ed30 ====

undefined8 FUN_18000ed30(longlong param_1)

{
  PyErr_Format(*(undefined8 *)PyExc_TypeError_exref,"cannot pickle \'%.200s\' object",
               *(undefined8 *)(*(longlong *)(param_1 + 8) + 0x18));
  return 0;
}



// ==== FUN_18000ed60 @ 18000ed60 ====

longlong *
FUN_18000ed60(uint param_1,undefined8 *param_2,undefined8 param_3,undefined8 param_4,
             longlong *param_5,undefined8 param_6)

{
  int *piVar1;
  longlong lVar2;
  longlong *plVar3;
  longlong lVar4;
  longlong *plVar5;
  void *_Dst;
  longlong *unaff_RBP;
  ulonglong uVar6;
  longlong *plVar7;
  undefined8 *puVar8;
  longlong *plVar9;
  
  uVar6 = (ulonglong)(param_1 >> 3 & 0xf);
  plVar5 = (longlong *)0x0;
  plVar3 = (longlong *)PyTuple_New(uVar6);
  if (plVar3 == (longlong *)0x0) {
    return unaff_RBP;
  }
  if (uVar6 != 0) {
    puVar8 = param_2;
    do {
      piVar1 = (int *)*puVar8;
      if (*piVar1 + 1 != 0) {
        *piVar1 = *piVar1 + 1;
      }
      *(int **)((longlong)puVar8 + (longlong)plVar3 + (0x18 - (longlong)param_2)) = piVar1;
      puVar8 = puVar8 + 1;
      uVar6 = uVar6 - 1;
    } while (uVar6 != 0);
  }
  lVar4 = PyDict_SetDefault(param_6,plVar3,plVar3);
  if (lVar4 == 0) goto LAB_18000ef22;
  plVar7 = DAT_180016750;
  plVar9 = DAT_180016750;
  if (param_5 == (longlong *)0x0) {
LAB_18000ee67:
    lVar4 = PyUnstable_Code_NewWithPosOnlyArgs
                      (param_1 & 1,param_1 >> 1 & 1,param_1 >> 2 & 1,param_1 >> 3 & 0xf,0,
                       param_1 >> 7 & 0x3ff,plVar7,DAT_180016748,DAT_180016748,lVar4,DAT_180016748,
                       DAT_180016748,param_3,param_4,param_4,param_1 >> 0x11 & 0x7f,plVar9,
                       DAT_180016750);
    if (lVar4 != 0) {
      *(undefined4 *)(lVar4 + 0xb8) = 0;
    }
    if (plVar5 == (longlong *)0x0) goto LAB_18000ef22;
  }
  else {
    lVar2 = param_5[2];
    plVar5 = (longlong *)PyBytes_FromStringAndSize(0);
    if (plVar5 == (longlong *)0x0) goto LAB_18000ef22;
    _Dst = (void *)PyBytes_AsString(plVar5);
    if (_Dst != (void *)0x0) {
      memset(_Dst,0,lVar2 * 2 + 4U & 0xfffffffffffffffc);
      plVar7 = plVar5;
      plVar9 = param_5;
      goto LAB_18000ee67;
    }
  }
  if ((-1 < (int)*plVar5) && (*plVar5 = *plVar5 + -1, *plVar5 == 0)) {
    _Py_Dealloc(plVar5);
  }
LAB_18000ef22:
  if ((-1 < (int)*plVar3) && (*plVar3 = *plVar3 + -1, *plVar3 == 0)) {
    _Py_Dealloc(plVar3);
  }
  return unaff_RBP;
}



// ==== FUN_18000ef60 @ 18000ef60 ====

void FUN_18000ef60(undefined *param_1)

{
  if (((code *)param_1 != _Py_NoneStruct_exref && (code *)param_1 != _Py_FalseStruct_exref) &&
      (code *)param_1 != _Py_TrueStruct_exref) {
                    /* WARNING: Could not recover jumptable at 0x00018000ef8f. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    PyObject_IsTrue();
    return;
  }
  return;
}



// ==== __security_check_cookie @ 18000efc0 ====

/* WARNING: This is an inlined function */

void __cdecl __security_check_cookie(uintptr_t _StackCookie)

{
  if ((_StackCookie == DAT_180015000) && ((short)(_StackCookie >> 0x30) == 0)) {
    return;
  }
  FUN_18000f368();
  return;
}



// ==== FUN_18000efe0 @ 18000efe0 ====

ulonglong FUN_18000efe0(undefined8 param_1,int param_2,longlong param_3)

{
  byte bVar1;
  undefined1 uVar2;
  ulonglong uVar3;
  undefined7 extraout_var;
  
  if (param_2 == 0) {
    uVar2 = FUN_18000f148(CONCAT71((int7)((ulonglong)param_1 >> 8),param_3 != 0));
    return CONCAT71(extraout_var,uVar2);
  }
  if (param_2 != 1) {
    if (param_2 == 2) {
      bVar1 = FUN_18000f654();
    }
    else {
      if (param_2 != 3) {
        return 1;
      }
      bVar1 = FUN_18000f67c();
    }
    return (ulonglong)bVar1;
  }
  uVar3 = FUN_18000f030(param_1,param_3);
  return uVar3;
}



// ==== FUN_18000f030 @ 18000f030 ====

undefined8 FUN_18000f030(undefined8 param_1,undefined8 param_2)

{
  bool bVar1;
  bool bVar2;
  int iVar3;
  undefined8 uVar4;
  undefined8 uVar5;
  longlong *plVar6;
  ulonglong uVar7;
  
  uVar4 = FUN_18000f738(0);
  if ((char)uVar4 != '\0') {
    uVar4 = __scrt_acquire_startup_lock();
    bVar1 = true;
    if (DAT_1800166d0 != 0) {
                    /* WARNING: Subroutine does not return */
      FUN_18000f8fc(7);
    }
    DAT_1800166d0 = 1;
    bVar2 = FUN_18000f63c();
    if (bVar2) {
      FUN_18000fa48();
      FUN_18000f584();
      FUN_18000f5b0();
      iVar3 = _initterm_e(&DAT_180010620,&DAT_180010628);
      if ((iVar3 == 0) && (uVar5 = __scrt_dllmain_after_initialize_c(), (char)uVar5 != '\0')) {
        _initterm(&DAT_180010610,&DAT_180010618);
        DAT_1800166d0 = 2;
        bVar1 = false;
      }
    }
    __scrt_release_startup_lock((char)uVar4);
    if (!bVar1) {
      plVar6 = (longlong *)FUN_18000f8e8();
      if ((*plVar6 != 0) && (uVar7 = FUN_18000f800((longlong)plVar6), (char)uVar7 != '\0')) {
        (*(code *)PTR__guard_dispatch_icall_1800105e8)(param_1,2,param_2);
      }
      DAT_180016130 = DAT_180016130 + 1;
      return 1;
    }
  }
  return 0;
}



// ==== FUN_18000f148 @ 18000f148 ====

undefined1 FUN_18000f148(undefined8 param_1)

{
  undefined1 uVar1;
  undefined8 uVar2;
  undefined7 uVar3;
  
  uVar1 = (undefined1)param_1;
  if (DAT_180016130 < 1) {
    uVar1 = 0;
  }
  else {
    DAT_180016130 = DAT_180016130 + -1;
    uVar2 = __scrt_acquire_startup_lock();
    if (DAT_1800166d0 != 2) {
                    /* WARNING: Subroutine does not return */
      FUN_18000f8fc(7);
    }
    __scrt_dllmain_uninitialize_c();
    FUN_18000f594();
    FUN_18000fa84();
    DAT_1800166d0 = 0;
    uVar3 = (undefined7)((ulonglong)param_1 >> 8);
    __scrt_release_startup_lock((char)uVar2);
    uVar1 = __scrt_uninitialize_crt(CONCAT71(uVar3,uVar1),'\0');
    FUN_18000f724();
  }
  return uVar1;
}



// ==== FUN_18000f1cc @ 18000f1cc ====

int FUN_18000f1cc(HMODULE param_1,int param_2,longlong param_3)

{
  ulonglong uVar1;
  undefined8 uVar2;
  HMODULE pHVar3;
  int iVar4;
  
  if ((param_2 == 0) && (DAT_180016130 < 1)) {
    return 0;
  }
  if (param_2 - 1U < 2) {
    if (DAT_180010650 == 0) {
      iVar4 = 1;
    }
    else {
      iVar4 = (*(code *)PTR__guard_dispatch_icall_1800105e8)();
    }
    if (iVar4 == 0) {
      return 0;
    }
    uVar1 = FUN_18000efe0(param_1,param_2,param_3);
    if ((int)uVar1 == 0) {
      return 0;
    }
  }
  uVar2 = FUN_18000f560(param_1,param_2);
  iVar4 = (int)uVar2;
  if ((param_2 == 1) && (iVar4 == 0)) {
    pHVar3 = param_1;
    FUN_18000f560(param_1,0);
    FUN_18000f148(CONCAT71((int7)((ulonglong)pHVar3 >> 8),param_3 != 0));
    if (DAT_180010650 != 0) {
      (*(code *)PTR__guard_dispatch_icall_1800105e8)(param_1,0,param_3);
    }
  }
  if ((param_2 == 0) || (param_2 == 3)) {
    uVar1 = FUN_18000efe0(param_1,param_2,param_3);
    iVar4 = 0;
    if ((int)uVar1 != 0) {
      if (DAT_180010650 == 0) {
        iVar4 = 1;
      }
      else {
        iVar4 = (*(code *)PTR__guard_dispatch_icall_1800105e8)(param_1,param_2,param_3);
      }
    }
  }
  return iVar4;
}



// ==== entry @ 18000f2f4 ====

void entry(HMODULE param_1,int param_2,longlong param_3)

{
  if (param_2 == 1) {
    FUN_18000f4b0();
  }
  FUN_18000f1cc(param_1,param_2,param_3);
  return;
}



// ==== __raise_securityfailure @ 18000f334 ====

/* Library Function - Single Match
    __raise_securityfailure
   
   Libraries: Visual Studio 2015 Release, Visual Studio 2017 Release, Visual Studio 2019 Release */

void __raise_securityfailure(_EXCEPTION_POINTERS *param_1)

{
  HANDLE pvVar1;
  
  SetUnhandledExceptionFilter((LPTOP_LEVEL_EXCEPTION_FILTER)0x0);
  UnhandledExceptionFilter(param_1);
  pvVar1 = GetCurrentProcess();
                    /* WARNING: Could not recover jumptable at 0x00018000f361. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  TerminateProcess(pvVar1,0xc0000409);
  return;
}



// ==== FUN_18000f368 @ 18000f368 ====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_18000f368(void)

{
  code *pcVar1;
  BOOL BVar2;
  undefined1 *puVar3;
  undefined1 auStack_38 [8];
  undefined1 auStack_30 [48];
  
  puVar3 = auStack_38;
  BVar2 = IsProcessorFeaturePresent(0x17);
  if (BVar2 != 0) {
    pcVar1 = (code *)swi(0x29);
    (*pcVar1)(2);
    puVar3 = auStack_30;
  }
  *(undefined8 *)(puVar3 + -8) = 0x18000f393;
  FUN_18000f43c((PCONTEXT)&DAT_1800161e0);
  _DAT_180016150 = *(undefined8 *)(puVar3 + 0x38);
  _DAT_180016278 = puVar3 + 0x40;
  _DAT_180016260 = *(undefined8 *)(puVar3 + 0x40);
  _DAT_180016140 = 0xc0000409;
  _DAT_180016144 = 1;
  _DAT_180016158 = 1;
  DAT_180016160 = 2;
  *(undefined8 *)(puVar3 + 0x20) = DAT_180015000;
  *(undefined8 *)(puVar3 + 0x28) = DAT_180015040;
  *(undefined8 *)(puVar3 + -8) = 0x18000f435;
  DAT_1800162d8 = _DAT_180016150;
  __raise_securityfailure((_EXCEPTION_POINTERS *)&PTR_DAT_180010658);
  return;
}



// ==== FUN_18000f43c @ 18000f43c ====

void FUN_18000f43c(PCONTEXT param_1)

{
  DWORD64 ControlPc;
  PRUNTIME_FUNCTION FunctionEntry;
  int iVar1;
  DWORD64 local_res8;
  ulonglong local_res10;
  PVOID local_res18 [2];
  
  RtlCaptureContext();
  ControlPc = param_1->Rip;
  iVar1 = 0;
  do {
    FunctionEntry = RtlLookupFunctionEntry(ControlPc,&local_res8,(PUNWIND_HISTORY_TABLE)0x0);
    if (FunctionEntry == (PRUNTIME_FUNCTION)0x0) {
      return;
    }
    RtlVirtualUnwind(0,local_res8,ControlPc,FunctionEntry,param_1,local_res18,&local_res10,
                     (PKNONVOLATILE_CONTEXT_POINTERS)0x0);
    iVar1 = iVar1 + 1;
  } while (iVar1 < 2);
  return;
}



// ==== FUN_18000f4b0 @ 18000f4b0 ====

void FUN_18000f4b0(void)

{
  DWORD DVar1;
  _FILETIME local_res8;
  LARGE_INTEGER local_res10;
  _FILETIME local_18 [2];
  
  if (DAT_180015000 == 0x2b992ddfa232) {
    local_res8.dwLowDateTime = 0;
    local_res8.dwHighDateTime = 0;
    GetSystemTimeAsFileTime(&local_res8);
    local_18[0] = local_res8;
    DVar1 = GetCurrentThreadId();
    local_18[0] = (_FILETIME)((ulonglong)local_18[0] ^ (ulonglong)DVar1);
    DVar1 = GetCurrentProcessId();
    local_18[0] = (_FILETIME)((ulonglong)local_18[0] ^ (ulonglong)DVar1);
    QueryPerformanceCounter(&local_res10);
    DAT_180015000 =
         ((ulonglong)local_res10.s.LowPart << 0x20 ^
          CONCAT44(local_res10.s.HighPart,local_res10.s.LowPart) ^ (ulonglong)local_18[0] ^
         (ulonglong)local_18) & 0xffffffffffff;
    if (DAT_180015000 == 0x2b992ddfa232) {
      DAT_180015000 = 0x2b992ddfa233;
    }
  }
  DAT_180015040 = ~DAT_180015000;
  return;
}



// ==== FUN_18000f560 @ 18000f560 ====

undefined8 FUN_18000f560(HMODULE param_1,int param_2)

{
  if ((param_2 == 1) && (DAT_180010650 == 0)) {
    DisableThreadLibraryCalls(param_1);
  }
  return 1;
}



// ==== FUN_18000f584 @ 18000f584 ====

void FUN_18000f584(void)

{
                    /* WARNING: Could not recover jumptable at 0x00018000f58b. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  InitializeSListHead(&DAT_1800166b0);
  return;
}



// ==== FUN_18000f594 @ 18000f594 ====

void FUN_18000f594(void)

{
  __std_type_info_destroy_list(&DAT_1800166b0);
  return;
}



// ==== FUN_18000f5a0 @ 18000f5a0 ====

undefined * FUN_18000f5a0(void)

{
  return &DAT_1800166c0;
}



// ==== FUN_18000f5a8 @ 18000f5a8 ====

undefined * FUN_18000f5a8(void)

{
  return &DAT_1800166c8;
}



// ==== FUN_18000f5b0 @ 18000f5b0 ====

void FUN_18000f5b0(void)

{
  ulonglong *puVar1;
  
  puVar1 = (ulonglong *)FUN_18000f5a0();
  *puVar1 = *puVar1 | 0x24;
  puVar1 = (ulonglong *)FUN_18000f5a8();
  *puVar1 = *puVar1 | 2;
  return;
}



// ==== __scrt_acquire_startup_lock @ 18000f5cc ====

/* Library Function - Single Match
    __scrt_acquire_startup_lock
   
   Libraries: Visual Studio 2015 Release, Visual Studio 2017 Release, Visual Studio 2019 Release */

ulonglong __scrt_acquire_startup_lock(void)

{
  ulonglong uVar1;
  bool bVar2;
  undefined7 extraout_var;
  ulonglong uVar3;
  
  bVar2 = __scrt_is_ucrt_dll_in_use();
  uVar3 = CONCAT71(extraout_var,bVar2);
  if ((int)uVar3 == 0) {
LAB_18000f5fa:
    uVar3 = uVar3 & 0xffffffffffffff00;
  }
  else {
    do {
      uVar3 = 0;
      LOCK();
      bVar2 = DAT_1800166d8 == 0;
      uVar1 = *(ulonglong *)((longlong)Self + 8);
      if (!bVar2) {
        uVar3 = DAT_1800166d8;
        uVar1 = DAT_1800166d8;
      }
      DAT_1800166d8 = uVar1;
      UNLOCK();
      if (bVar2) goto LAB_18000f5fa;
    } while (*(ulonglong *)((longlong)Self + 8) != uVar3);
    uVar3 = CONCAT71((int7)(uVar3 >> 8),1);
  }
  return uVar3;
}



// ==== __scrt_dllmain_after_initialize_c @ 18000f608 ====

/* Library Function - Single Match
    __scrt_dllmain_after_initialize_c
   
   Libraries: Visual Studio 2015 Release, Visual Studio 2017 Release, Visual Studio 2019 Release */

undefined8 __scrt_dllmain_after_initialize_c(void)

{
  bool bVar1;
  undefined7 extraout_var;
  undefined8 uVar2;
  ulonglong uVar3;
  
  bVar1 = __scrt_is_ucrt_dll_in_use();
  if ((int)CONCAT71(extraout_var,bVar1) == 0) {
    uVar3 = FUN_18000fd5c();
    uVar3 = _configure_narrow_argv(uVar3 & 0xffffffff);
    if ((int)uVar3 != 0) {
      return uVar3 & 0xffffffffffffff00;
    }
    uVar2 = _initialize_narrow_environment();
  }
  else {
    uVar2 = FUN_18000fac4();
  }
  return CONCAT71((int7)((ulonglong)uVar2 >> 8),1);
}



// ==== FUN_18000f63c @ 18000f63c ====

bool FUN_18000f63c(void)

{
  undefined8 uVar1;
  
  uVar1 = FUN_18000f774(0);
  return (char)uVar1 != '\0';
}



// ==== FUN_18000f654 @ 18000f654 ====

undefined1 FUN_18000f654(void)

{
  char cVar1;
  
  cVar1 = FUN_18000fdb4();
  if (cVar1 != '\0') {
    cVar1 = FUN_18000fdb4();
    if (cVar1 != '\0') {
      return 1;
    }
    FUN_18000fdb4();
  }
  return 0;
}



// ==== FUN_18000f67c @ 18000f67c ====

undefined1 FUN_18000f67c(void)

{
  FUN_18000fdb4();
  FUN_18000fdb4();
  return 1;
}



// ==== __scrt_dllmain_exception_filter @ 18000f694 ====

/* Library Function - Single Match
    __scrt_dllmain_exception_filter
   
   Libraries: Visual Studio 2017 Release, Visual Studio 2019 Release */

void __scrt_dllmain_exception_filter
               (undefined8 param_1,int param_2,undefined8 param_3,undefined *param_4,
               undefined4 param_5,undefined8 param_6)

{
  bool bVar1;
  undefined7 extraout_var;
  
  bVar1 = __scrt_is_ucrt_dll_in_use();
  if (((int)CONCAT71(extraout_var,bVar1) == 0) && (param_2 == 1)) {
    (*(code *)PTR__guard_dispatch_icall_1800105e8)(param_1,0,param_3);
  }
  _seh_filter_dll(param_5,param_6);
  return;
}



// ==== __scrt_dllmain_uninitialize_c @ 18000f6f4 ====

/* Library Function - Single Match
    __scrt_dllmain_uninitialize_c
   
   Libraries: Visual Studio 2015 Release, Visual Studio 2017 Release, Visual Studio 2019 Release */

void __scrt_dllmain_uninitialize_c(void)

{
  bool bVar1;
  undefined7 extraout_var;
  undefined8 uVar2;
  
  bVar1 = __scrt_is_ucrt_dll_in_use();
  if ((int)CONCAT71(extraout_var,bVar1) != 0) {
    _execute_onexit_table(&DAT_1800166e8);
    return;
  }
  uVar2 = FUN_18000fdb8();
  if ((int)uVar2 == 0) {
    _cexit();
  }
  return;
}



// ==== FUN_18000f724 @ 18000f724 ====

void FUN_18000f724(void)

{
  FUN_18000fdb4();
  FUN_18000fdb4();
  return;
}



// ==== FUN_18000f738 @ 18000f738 ====

longlong FUN_18000f738(int param_1)

{
  char cVar1;
  uint7 extraout_var;
  uint7 uVar2;
  undefined7 extraout_var_00;
  uint7 extraout_var_01;
  
  if (param_1 == 0) {
    DAT_1800166e0 = 1;
  }
  FUN_18000fac4();
  cVar1 = FUN_18000fdb4();
  uVar2 = extraout_var;
  if (cVar1 != '\0') {
    cVar1 = FUN_18000fdb4();
    if (cVar1 != '\0') {
      return CONCAT71(extraout_var_00,1);
    }
    FUN_18000fdb4();
    uVar2 = extraout_var_01;
  }
  return (ulonglong)uVar2 << 8;
}



// ==== FUN_18000f774 @ 18000f774 ====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined8 FUN_18000f774(uint param_1)

{
  bool bVar1;
  ulonglong in_RAX;
  undefined7 extraout_var;
  
  if (DAT_1800166e1 == '\0') {
    if (1 < param_1) {
                    /* WARNING: Subroutine does not return */
      FUN_18000f8fc(5);
    }
    bVar1 = __scrt_is_ucrt_dll_in_use();
    if (((int)CONCAT71(extraout_var,bVar1) == 0) || (param_1 != 0)) {
      in_RAX = 0xffffffffffffffff;
      _DAT_1800166e8 = _DAT_180010670;
      uRam00000001800166f0 = _UNK_180010678;
      _DAT_1800166f8 = 0xffffffffffffffff;
      _DAT_180016700 = _DAT_180010670;
      uRam0000000180016708 = _UNK_180010678;
      _DAT_180016710 = 0xffffffffffffffff;
    }
    else {
      in_RAX = _initialize_onexit_table(&DAT_1800166e8);
      if (((int)in_RAX != 0) ||
         (in_RAX = _initialize_onexit_table(&DAT_180016700), (int)in_RAX != 0)) {
        return in_RAX & 0xffffffffffffff00;
      }
    }
    DAT_1800166e1 = '\x01';
  }
  return CONCAT71((int7)(in_RAX >> 8),1);
}



// ==== FUN_18000f800 @ 18000f800 ====

ulonglong FUN_18000f800(longlong param_1)

{
  ulonglong uVar1;
  uint7 uVar2;
  longlong lVar3;
  longlong lVar4;
  
  uVar1 = 0x5a4d;
  if (IMAGE_DOS_HEADER_180000000.e_magic == (char  [2])0x5a4d) {
    lVar3 = (longlong)(int)IMAGE_DOS_HEADER_180000000.e_lfanew;
    if ((*(int *)(lVar3 + 0x180000000) == 0x4550) &&
       (uVar1 = 0x20b,
       *(short *)((longlong)IMAGE_DOS_HEADER_180000000.e_res_4_ + lVar3 + -4) == 0x20b)) {
      lVar4 = (ulonglong)*(ushort *)((longlong)IMAGE_DOS_HEADER_180000000.e_res_4_ + lVar3 + -8) +
              0x18 + lVar3 + 0x180000000;
      uVar1 = (ulonglong)*(ushort *)(IMAGE_DOS_HEADER_180000000.e_magic + lVar3 + 6);
      lVar3 = lVar4 + uVar1 * 0x28;
      for (; lVar4 != lVar3; lVar4 = lVar4 + 0x28) {
        if (((ulonglong)*(uint *)(lVar4 + 0xc) <= param_1 - 0x180000000U) &&
           (uVar1 = (ulonglong)(*(int *)(lVar4 + 8) + *(uint *)(lVar4 + 0xc)),
           param_1 - 0x180000000U < uVar1)) goto LAB_18000f876;
      }
      lVar4 = 0;
LAB_18000f876:
      if (lVar4 == 0) {
        return uVar1 & 0xffffffffffffff00;
      }
      uVar2 = (uint7)(uVar1 >> 8);
      if (*(int *)(lVar4 + 0x24) < 0) {
        return (ulonglong)uVar2 << 8;
      }
      return CONCAT71(uVar2,1);
    }
  }
  return uVar1 & 0xffffffffffffff00;
}



// ==== __scrt_release_startup_lock @ 18000f898 ====

/* Library Function - Single Match
    __scrt_release_startup_lock
   
   Libraries: Visual Studio 2015 Release, Visual Studio 2017 Release, Visual Studio 2019 Release */

void __scrt_release_startup_lock(char param_1)

{
  bool bVar1;
  undefined3 extraout_var;
  
  bVar1 = __scrt_is_ucrt_dll_in_use();
  if ((CONCAT31(extraout_var,bVar1) != 0) && (param_1 == '\0')) {
    LOCK();
    DAT_1800166d8 = 0;
    UNLOCK();
  }
  return;
}



// ==== __scrt_uninitialize_crt @ 18000f8bc ====

/* Library Function - Single Match
    __scrt_uninitialize_crt
   
   Library: Visual Studio 2019 Release */

undefined1 __scrt_uninitialize_crt(undefined8 param_1,char param_2)

{
  if ((DAT_1800166e0 == '\0') || (param_2 == '\0')) {
    FUN_18000fdb4();
    FUN_18000fdb4();
  }
  return 1;
}



// ==== FUN_18000f8e8 @ 18000f8e8 ====

undefined * FUN_18000f8e8(void)

{
  return &DAT_180016de8;
}



// ==== FUN_18000f8f0 @ 18000f8f0 ====

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_18000f8f0(void)

{
  _DAT_180016718 = 0;
  return;
}



// ==== FUN_18000f8fc @ 18000f8fc ====

void FUN_18000f8fc(undefined4 param_1)

{
  code *pcVar1;
  BOOL BVar2;
  LONG LVar3;
  PRUNTIME_FUNCTION FunctionEntry;
  undefined1 *puVar4;
  undefined8 unaff_retaddr;
  DWORD64 local_res10;
  undefined1 local_res18 [8];
  undefined1 local_res20 [8];
  undefined1 auStack_5c8 [8];
  undefined1 auStack_5c0 [232];
  undefined1 local_4d8 [152];
  undefined1 *local_440;
  DWORD64 local_3e0;
  
  puVar4 = auStack_5c8;
  BVar2 = IsProcessorFeaturePresent(0x17);
  if (BVar2 != 0) {
    pcVar1 = (code *)swi(0x29);
    (*pcVar1)(param_1);
    puVar4 = auStack_5c0;
  }
  *(undefined8 *)(puVar4 + -8) = 0x18000f930;
  FUN_18000f8f0();
  *(undefined8 *)(puVar4 + -8) = 0x18000f941;
  memset(local_4d8,0,0x4d0);
  *(undefined8 *)(puVar4 + -8) = 0x18000f94b;
  RtlCaptureContext(local_4d8);
  *(undefined8 *)(puVar4 + -8) = 0x18000f965;
  FunctionEntry = RtlLookupFunctionEntry(local_3e0,&local_res10,(PUNWIND_HISTORY_TABLE)0x0);
  if (FunctionEntry != (PRUNTIME_FUNCTION)0x0) {
    *(undefined8 *)(puVar4 + 0x38) = 0;
    *(undefined1 **)(puVar4 + 0x30) = local_res18;
    *(undefined1 **)(puVar4 + 0x28) = local_res20;
    *(undefined1 **)(puVar4 + 0x20) = local_4d8;
    *(undefined8 *)(puVar4 + -8) = 0x18000f9a9;
    RtlVirtualUnwind(0,local_res10,local_3e0,FunctionEntry,*(PCONTEXT *)(puVar4 + 0x20),
                     *(PVOID **)(puVar4 + 0x28),*(PDWORD64 *)(puVar4 + 0x30),
                     *(PKNONVOLATILE_CONTEXT_POINTERS *)(puVar4 + 0x38));
  }
  local_440 = &stack0x00000008;
  *(undefined8 *)(puVar4 + -8) = 0x18000f9db;
  memset(puVar4 + 0x50,0,0x98);
  *(undefined8 *)(puVar4 + 0x60) = unaff_retaddr;
  *(undefined4 *)(puVar4 + 0x50) = 0x40000015;
  *(undefined4 *)(puVar4 + 0x54) = 1;
  *(undefined8 *)(puVar4 + -8) = 0x18000f9fd;
  BVar2 = IsDebuggerPresent();
  *(undefined1 **)(puVar4 + 0x40) = puVar4 + 0x50;
  *(undefined1 **)(puVar4 + 0x48) = local_4d8;
  *(undefined8 *)(puVar4 + -8) = 0x18000fa1a;
  SetUnhandledExceptionFilter((LPTOP_LEVEL_EXCEPTION_FILTER)0x0);
  *(undefined8 *)(puVar4 + -8) = 0x18000fa25;
  LVar3 = UnhandledExceptionFilter((_EXCEPTION_POINTERS *)(puVar4 + 0x40));
  if ((LVar3 == 0) && (BVar2 != 1)) {
    *(undefined8 *)(puVar4 + -8) = 0x18000fa36;
    FUN_18000f8f0();
  }
  return;
}



// ==== FUN_18000fa48 @ 18000fa48 ====

void FUN_18000fa48(void)

{
  longlong *plVar1;
  
  for (plVar1 = &DAT_180012250; plVar1 < &DAT_180012250; plVar1 = plVar1 + 1) {
    if (*plVar1 != 0) {
      (*(code *)PTR__guard_dispatch_icall_1800105e8)();
    }
  }
  return;
}



// ==== FUN_18000fa84 @ 18000fa84 ====

void FUN_18000fa84(void)

{
  longlong *plVar1;
  
  for (plVar1 = &DAT_180012260; plVar1 < &DAT_180012260; plVar1 = plVar1 + 1) {
    if (*plVar1 != 0) {
      (*(code *)PTR__guard_dispatch_icall_1800105e8)();
    }
  }
  return;
}



// ==== _guard_check_icall @ 18000fac0 ====

void _guard_check_icall(void)

{
  return;
}



// ==== FUN_18000fac4 @ 18000fac4 ====

/* WARNING: Removing unreachable block (ram,0x00018000fbb5) */
/* WARNING: Removing unreachable block (ram,0x00018000fba5) */
/* WARNING: Removing unreachable block (ram,0x00018000fb80) */
/* WARNING: Removing unreachable block (ram,0x00018000fafe) */
/* WARNING: Removing unreachable block (ram,0x00018000fadc) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined8 FUN_18000fac4(void)

{
  int *piVar1;
  uint *puVar2;
  int *piVar3;
  longlong lVar4;
  uint uVar5;
  byte bVar6;
  ulonglong uVar7;
  uint uVar8;
  ulonglong uVar9;
  uint uVar10;
  uint uVar11;
  ulonglong uVar12;
  ulonglong in_XCR0;
  
  piVar1 = (int *)cpuid_basic_info(0);
  puVar2 = (uint *)cpuid_Version_info(1);
  uVar5 = puVar2[3];
  if ((piVar1[2] == 0x49656e69 && piVar1[3] == 0x6c65746e) && piVar1[1] == 0x756e6547) {
    uVar8 = *puVar2 & 0xfff3ff0;
    _DAT_180015060 = 0x8000;
    _DAT_180015068 = 0xffffffffffffffff;
    if ((((uVar8 == 0x106c0) || (uVar8 == 0x20660)) || (uVar8 == 0x20670)) ||
       ((uVar8 - 0x30650 < 0x21 &&
        ((0x100010001U >> ((ulonglong)(uVar8 - 0x30650) & 0x3f) & 1) != 0)))) {
      DAT_180016720 = DAT_180016720 | 1;
    }
  }
  uVar8 = 0;
  uVar10 = 0;
  uVar11 = 0;
  uVar12 = 0;
  if (6 < *piVar1) {
    piVar3 = (int *)cpuid_Extended_Feature_Enumeration_info(7);
    uVar8 = piVar3[1];
    uVar10 = piVar3[2];
    if ((uVar8 >> 9 & 1) != 0) {
      DAT_180016720 = DAT_180016720 | 2;
    }
    if (0 < *piVar3) {
      lVar4 = cpuid_Extended_Feature_Enumeration_info(7);
      uVar11 = *(uint *)(lVar4 + 8);
    }
    if (0x23 < *piVar1) {
      lVar4 = cpuid(0x24);
      uVar12 = (ulonglong)*(uint *)(lVar4 + 4);
    }
  }
  _DAT_180015058 = 1;
  DAT_18001505c = 2;
  uVar9 = DAT_180015050 & 0xfffffffffffffffe;
  if ((uVar5 >> 0x14 & 1) != 0) {
    _DAT_180015058 = 2;
    DAT_18001505c = 6;
    uVar9 = DAT_180015050 & 0xffffffffffffffee;
  }
  DAT_180015050 = uVar9;
  if ((uVar5 >> 0x1b & 1) != 0) {
    uVar9 = xinuse(0);
    uVar9 = in_XCR0 & uVar9 & 0xffffffff;
    if (((uVar5 >> 0x1c & 1) != 0) && (bVar6 = (byte)uVar9, (bVar6 & 6) == 6)) {
      _DAT_180015058 = 3;
      uVar7 = DAT_180015050;
      uVar5 = DAT_18001505c | 8;
      if ((uVar8 & 0x20) != 0) {
        _DAT_180015058 = 5;
        uVar7 = DAT_180015050 & 0xfffffffffffffffd;
        uVar5 = DAT_18001505c | 0x28;
        if (((uVar8 & 0xd0030000) == 0xd0030000) && ((bVar6 & 0xe0) == 0xe0)) {
          DAT_18001505c = DAT_18001505c | 0x68;
          _DAT_180015058 = 6;
          uVar7 = DAT_180015050 & 0xffffffffffffffd9;
          uVar5 = DAT_18001505c;
        }
      }
      DAT_18001505c = uVar5;
      DAT_180015050 = uVar7;
      if ((uVar10 >> 0x17 & 1) != 0) {
        DAT_180015050 = DAT_180015050 & 0xfffffffffeffffff;
      }
      if (((uVar11 >> 0x13 & 1) != 0) && ((bVar6 & 0xe0) == 0xe0)) {
        _DAT_18001671c = (uint)uVar12 & 0x400ff;
        DAT_180015050 = ~((ulonglong)((uint)(uVar12 >> 0x10) & 6) | 0x1000029) & DAT_180015050;
        if (1 < (byte)_DAT_18001671c) {
          DAT_180015050 = DAT_180015050 & 0xffffffffffffffbf;
        }
      }
    }
    if (((uVar11 >> 0x15 & 1) != 0) && ((uVar9 >> 0x13 & 1) != 0)) {
      DAT_180015050 = DAT_180015050 & 0xffffffffffffff7f;
    }
  }
  return 0;
}



// ==== FUN_18000fd5c @ 18000fd5c ====

undefined8 FUN_18000fd5c(void)

{
  return 1;
}



// ==== __scrt_is_ucrt_dll_in_use @ 18000fd64 ====

/* Library Function - Single Match
    __scrt_is_ucrt_dll_in_use
   
   Libraries: Visual Studio 2017 Release, Visual Studio 2019 Release */

bool __scrt_is_ucrt_dll_in_use(void)

{
  return DAT_180015070 != 0;
}



// ==== __std_type_info_destroy_list @ 18000fd76 ====

void __std_type_info_destroy_list(void)

{
                    /* WARNING: Could not recover jumptable at 0x00018000fd76. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  __std_type_info_destroy_list();
  return;
}



// ==== memset @ 18000fd7c ====

void * __cdecl memset(void *_Dst,int _Val,size_t _Size)

{
  void *pvVar1;
  
                    /* WARNING: Could not recover jumptable at 0x00018000fd7c. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  pvVar1 = memset(_Dst,_Val,_Size);
  return pvVar1;
}



// ==== _initterm @ 18000fd82 ====

void _initterm(void)

{
                    /* WARNING: Could not recover jumptable at 0x00018000fd82. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  _initterm();
  return;
}



// ==== _initterm_e @ 18000fd88 ====

void _initterm_e(void)

{
                    /* WARNING: Could not recover jumptable at 0x00018000fd88. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  _initterm_e();
  return;
}



// ==== _seh_filter_dll @ 18000fd8e ====

void _seh_filter_dll(void)

{
                    /* WARNING: Could not recover jumptable at 0x00018000fd8e. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  _seh_filter_dll();
  return;
}



// ==== _configure_narrow_argv @ 18000fd94 ====

void _configure_narrow_argv(void)

{
                    /* WARNING: Could not recover jumptable at 0x00018000fd94. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  _configure_narrow_argv();
  return;
}



// ==== _initialize_narrow_environment @ 18000fd9a ====

void _initialize_narrow_environment(void)

{
                    /* WARNING: Could not recover jumptable at 0x00018000fd9a. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  _initialize_narrow_environment();
  return;
}



// ==== _initialize_onexit_table @ 18000fda0 ====

void _initialize_onexit_table(void)

{
                    /* WARNING: Could not recover jumptable at 0x00018000fda0. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  _initialize_onexit_table();
  return;
}



// ==== _execute_onexit_table @ 18000fda6 ====

void _execute_onexit_table(void)

{
                    /* WARNING: Could not recover jumptable at 0x00018000fda6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  _execute_onexit_table();
  return;
}



// ==== _cexit @ 18000fdac ====

void __cdecl _cexit(void)

{
                    /* WARNING: Could not recover jumptable at 0x00018000fdac. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  _cexit();
  return;
}



// ==== FUN_18000fdb4 @ 18000fdb4 ====

undefined1 FUN_18000fdb4(void)

{
  return 1;
}



// ==== FUN_18000fdb8 @ 18000fdb8 ====

undefined8 FUN_18000fdb8(void)

{
  return 0;
}



// ==== FUN_18000fdbc @ 18000fdbc ====

undefined8 FUN_18000fdbc(undefined8 param_1,undefined8 param_2,undefined8 param_3,longlong param_4)

{
  FUN_18000fddc(param_2,param_4);
  return 1;
}



// ==== FUN_18000fddc @ 18000fddc ====

/* WARNING: Function: __security_check_cookie replaced with injection: security_check_cookie */

ulonglong FUN_18000fddc(undefined8 param_1,longlong param_2)

{
  ulonglong uVar1;
  ulonglong uVar2;
  
  uVar2 = (ulonglong)*(uint *)(*(longlong *)(param_2 + 0x10) + 8);
  uVar1 = *(ulonglong *)(param_2 + 8);
  if ((*(byte *)(uVar2 + 3 + uVar1) & 0xf) != 0) {
    uVar1 = (ulonglong)*(byte *)(uVar2 + 3 + uVar1) & 0xfffffff0;
  }
  return uVar1;
}



// ==== memcmp @ 18000fe3c ====

int __cdecl memcmp(void *_Buf1,void *_Buf2,size_t _Size)

{
  int iVar1;
  
                    /* WARNING: Could not recover jumptable at 0x00018000fe3c. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  iVar1 = memcmp(_Buf1,_Buf2,_Size);
  return iVar1;
}



// ==== memcpy @ 18000fe42 ====

void * __cdecl memcpy(void *_Dst,void *_Src,size_t _Size)

{
  void *pvVar1;
  
                    /* WARNING: Could not recover jumptable at 0x00018000fe42. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  pvVar1 = memcpy(_Dst,_Src,_Size);
  return pvVar1;
}



// ==== _guard_dispatch_icall @ 18000fe60 ====

/* WARNING: This is an inlined function */

void _guard_dispatch_icall(void)

{
  code *UNRECOVERED_JUMPTABLE;
  
                    /* WARNING: Could not recover jumptable at 0x00018000fe60. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}



// ==== _guard_dispatch_icall @ 18000fe80 ====

/* WARNING: This is an inlined function */
/* WARNING: Switch with 1 destination removed at 0x00018000fe80 */

void _guard_dispatch_icall(void)

{
  code *UNRECOVERED_JUMPTABLE;
  
                    /* WARNING: Could not recover jumptable at 0x00018000fe60. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}



// ==== FUN_18000fe86 @ 18000fe86 ====

void FUN_18000fe86(undefined8 param_1,longlong param_2)

{
  __scrt_release_startup_lock(*(char *)(param_2 + 0x40));
  return;
}



// ==== FUN_18000fe9d @ 18000fe9d ====

void FUN_18000fe9d(undefined8 param_1,longlong param_2)

{
  __scrt_release_startup_lock(*(char *)(param_2 + 0x20));
  return;
}



// ==== FUN_18000feb6 @ 18000feb6 ====

void FUN_18000feb6(void)

{
  FUN_18000f724();
  return;
}



// ==== FUN_18000feca @ 18000feca ====

void FUN_18000feca(undefined8 *param_1,longlong param_2)

{
  __scrt_dllmain_exception_filter
            (*(undefined8 *)(param_2 + 0x60),*(int *)(param_2 + 0x68),
             *(undefined8 *)(param_2 + 0x70),FUN_18000efe0,*(undefined4 *)*param_1,param_1);
  return;
}



// ==== FUN_18000ff00 @ 18000ff00 ====

bool FUN_18000ff00(undefined8 *param_1)

{
  return *(int *)*param_1 == -0x3ffffffb;
}



// total funcoes decompiladas: 171
