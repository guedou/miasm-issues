#! /usr/bin/env python2
#-*- coding:utf-8 -*-

import unittest
import logging

from miasm2.ir.symbexec import SymbolicExecutionEngine
from miasm2.arch.arm.arch import mn_arm as mn
from miasm2.arch.arm.sem import ir_arml as ir_arch
from miasm2.arch.arm.regs import *
from miasm2.expression.expression import *
from miasm2.core.asmblock import AsmSymbolPool
from pdb import pm

logging.getLogger('cpuhelper').setLevel(logging.ERROR)
EXCLUDE_REGS = set([ir_arch().IRDst])

symbol_pool = AsmSymbolPool()

def M(addr):
    return ExprMem(ExprInt(addr, 16), 16)


def compute(asm, inputstate={}, debug=False):
    sympool = dict(regs_init)
    sympool.update({k: ExprInt(v, k.size) for k, v in inputstate.iteritems()})
    interm = ir_arch()
    symexec = SymbolicExecutionEngine(interm, sympool)
    instr = mn.fromstring(asm, symbol_pool, "l")
    code = mn.asm(instr)[0]
    instr = mn.dis(code, "l")
    instr.offset = inputstate.get(PC, 0)
    lbl = interm.add_instr(instr)
    symexec.run_at(lbl)
    if debug:
        for k, v in symexec.symbols.items():
            if regs_init.get(k, None) != v:
                print k, v
    out = {}
    for k, v in symexec.symbols.items():
        if k in EXCLUDE_REGS:
            continue
        elif regs_init.get(k, None) == v:
            continue
        elif isinstance(v, ExprInt):
            out[k] = v.arg.arg
        else:
            out[k] = v
    return out

class TestARMSemantic(unittest.TestCase):

    # def test_condition(self):
    # §A8.3:                   Conditional execution
    #    pass

    def test_shift(self):
        # §A8.4:                   Shifts applied to a register
        self.assertEqual(
            compute('MOV R4, R4       ', {R4: 0xDEADBEEF, }), {R4: 0xDEADBEEF, })
        self.assertRaises(ValueError, compute, 'MOV R4, R4 LSL  0')
        self.assertEqual(
            compute('MOV R4, R4 LSL  1', {R4: 0xDEADBEEF, }), {R4: 0xBD5B7DDE, })
        self.assertEqual(
            compute('MOV R4, R4 LSL 16', {R4: 0xDEADBEEF, }), {R4: 0xBEEF0000, })
        self.assertEqual(
            compute('MOV R4, R4 LSL 31', {R4: 0xDEADBEEF, }), {R4: 0x80000000, })
        self.assertRaises(ValueError, compute, 'MOV R4, R4 LSL 32')
        self.assertEqual(
            compute('MOV R4, R4 LSL R5', {R4: 0xDEADBEEF, R5: 0xBADBAD01, }), {R4: 0xBD5B7DDE, R5: 0xBADBAD01, })
        self.assertRaises(ValueError, compute, 'MOV R4, R4 LSR  0')
        self.assertEqual(
            compute('MOV R4, R4 LSR  1', {R4: 0xDEADBEEF, }), {R4: 0x6F56DF77, })
        self.assertEqual(
            compute('MOV R4, R4 LSR 16', {R4: 0xDEADBEEF, }), {R4: 0x0000DEAD, })
        self.assertEqual(
            compute('MOV R4, R4 LSR 31', {R4: 0xDEADBEEF, }), {R4: 0x00000001, })
        self.assertEqual(
            compute('MOV R4, R4 LSR 32', {R4: 0xDEADBEEF, }), {R4: 0xDEADBEEF, })
        self.assertRaises(ValueError, compute, 'MOV R4, R4 LSR 33')
        self.assertEqual(
            compute('MOV R4, R4 LSR R5', {R4: 0xDEADBEEF, R5: 0xBADBAD01, }), {R4: 0x6F56DF77, R5: 0xBADBAD01, })
        self.assertRaises(ValueError, compute, 'MOV R4, R4 ASR  0')
        self.assertEqual(
            compute('MOV R4, R4 ASR  1', {R4: 0xDEADBEEF, }), {R4: 0xEF56DF77, })
        self.assertEqual(
            compute('MOV R4, R4 ASR 16', {R4: 0xDEADBEEF, }), {R4: 0xFFFFDEAD, })
        self.assertEqual(
            compute('MOV R4, R4 ASR 31', {R4: 0xDEADBEEF, }), {R4: 0xFFFFFFFF, })
        self.assertEqual(
            compute('MOV R4, R4 ASR 32', {R4: 0xDEADBEEF, }), {R4: 0xDEADBEEF, })
        self.assertRaises(ValueError, compute, 'MOV R4, R4 ASR 33')
        self.assertEqual(
            compute('MOV R4, R4 ASR R5', {R4: 0xDEADBEEF, R5: 0xBADBAD01, }), {R4: 0xEF56DF77, R5: 0xBADBAD01, })
        self.assertRaises(ValueError, compute, 'MOV R4, R4 ROR  0')
        self.assertEqual(
            compute('MOV R4, R4 ROR  1', {R4: 0xDEADBEEF, }), {R4: 0xEF56DF77, })
        self.assertEqual(
            compute('MOV R4, R4 ROR 16', {R4: 0xDEADBEEF, }), {R4: 0xBEEFDEAD, })
        self.assertEqual(
            compute('MOV R4, R4 ROR 31', {R4: 0xDEADBEEF, }), {R4: 0xBD5B7DDF, })
        self.assertRaises(ValueError, compute, 'MOV R4, R4 ROR 32')
        self.assertEqual(
            compute('MOV R4, R4 ROR R5', {R4: 0xDEADBEEF, R5: 0xBADBAD01, }), {R4: 0xEF56DF77, R5: 0xBADBAD01, })
        self.assertEqual(compute('MOV R4, R4 RRX   ', {cf: 0, R4: 0xDEADBEEF, }), {
                         cf: 0, R4: 0x6F56DF77, })
        self.assertEqual(compute('MOV R4, R4 RRX   ', {cf: 1, R4: 0xDEADBEEF, }), {
                         cf: 1, R4: 0xEF56DF77, })

    def test_ADC(self):
        # §A8.8.1:                 ADC{S}{<c>}{<q>} {<Rd>,} <Rn>, #<const>
        self.assertRaises(
            ValueError, compute, 'ADC          R4,   0x00000001 ')
        self.assertEqual(compute('ADC                R4,    R4,   0x00000001 ',   {
                                 cf: 0, R4: 0x00000000, }), {cf: 0,     R4: 0x00000001, })
        self.assertEqual(compute('ADC                R4,    R4,   0x00000000 ',   {
                                 cf: 1, R4: 0x00000000, }), {cf: 1,     R4: 0x00000001, })
        self.assertEqual(compute('ADC                PC,    R4,   0x00000001 ',   {
                                 cf: 0, R4: 0xFFFFFFFF, PC: 0x55555555, }), {cf: 0,     R4: 0xFFFFFFFF, PC: 0x00000000, })
        self.assertEqual(compute('ADC                PC,    R4,   0x00000000 ',   {
                                 cf: 1, R4: 0xFFFFFFFF, PC: 0x55555555, }), {cf: 1,     R4: 0xFFFFFFFF, PC: 0x00000000, })
        self.assertEqual(compute('ADCS               R4,    R4,   0x80000000 ',   {cf: 0, R4: 0x80000000, }), {
                         nf: 0, zf: 1, cf: 1, of: 1, R4: 0x00000000, })
        self.assertEqual(compute('ADCS               R4,    R4,   0xFF000000 ',   {cf: 1, R4: 0x00FFFFFE, }), {
                         nf: 1, zf: 0, cf: 0, of: 0, R4: 0xFFFFFFFF, })
        self.assertEqual(compute('ADCS               PC,    R4,   0x00000000 ',   {
                                 cf: 0, R4: 0x00000000, PC: 0x55555555, }), {cf: 0,     R4: 0x00000000, PC: 0x00000000, })
        self.assertEqual(compute('ADCS               PC,    R4,   0xFF000000 ',   {
                                 cf: 1, R4: 0x01000000, PC: 0x55555555, }), {cf: 1,     R4: 0x01000000, PC: 0x00000001, })

        # §A8.8.2:                 ADC{S}{<c>}{<q>} {<Rd>,} <Rn>, <Rm> {,<shift>}
        self.assertRaises(
            ValueError, compute, 'ADC          R4,   R5          ')
        self.assertEqual(compute('ADC                R4,    R4,   R5          ',  {
                                 cf: 1, R4: 0xFFFFFFFF, R5: 0x00000000, }), {cf: 1,     R4: 0x00000000, R5: 0x00000000, })
        self.assertEqual(compute('ADC                R4,    R4,   R5    LSL 1 ',  {
                                 cf: 0, R4: 0x00000001, R5: 0x00000008, }), {cf: 0,     R4: 0x00000011, R5: 0x00000008, })
        self.assertEqual(compute('ADC                R4,    R4,   R5    LSR 2 ',  {
                                 cf: 1, R4: 0x00000000, R5: 0x80000041, }), {cf: 1,     R4: 0x20000011, R5: 0x80000041, })
        self.assertEqual(compute('ADC                R4,    R4,   R5    ASR 3 ',  {
                                 cf: 0, R4: 0x00000001, R5: 0x80000081, }), {cf: 0,     R4: 0xF0000011, R5: 0x80000081, })
        self.assertEqual(compute('ADC                R4,    R4,   R5    ROR 4 ',  {
                                 cf: 1, R4: 0xFFFFFFFF, R5: 0x0000010F, }), {cf: 1,     R4: 0xF0000010, R5: 0x0000010F, })
        self.assertEqual(compute('ADC                R4,    R4,   R5    RRX   ',  {
                                 cf: 1, R4: 0xFFFFFFFF, R5: 0x00000101, }), {cf: 1,     R4: 0x80000080, R5: 0x00000101, })
        self.assertEqual(compute('ADCS               R4,    R4,   R5          ',  {cf: 1, R4: 0xFFFFFFFF, R5: 0x00000000, }), {
                         nf: 0, zf: 1, cf: 1, of: 0, R4: 0x00000000, R5: 0x00000000, })
        self.assertEqual(compute('ADCS               R4,    R4,   R5    LSL 1 ',  {cf: 0, R4: 0x00000001, R5: 0x00000008, }), {
                         nf: 0, zf: 0, cf: 0, of: 0, R4: 0x00000011, R5: 0x00000008, })
        self.assertEqual(compute('ADCS               R4,    R4,   R5    LSR 2 ',  {cf: 1, R4: 0x00000000, R5: 0x80000041, }), {
                         nf: 0, zf: 0, cf: 0, of: 0, R4: 0x20000011, R5: 0x80000041, })
        self.assertEqual(compute('ADCS               R4,    R4,   R5    ASR 3 ',  {cf: 0, R4: 0x00000001, R5: 0x80000081, }), {
                         nf: 1, zf: 0, cf: 0, of: 0, R4: 0xF0000011, R5: 0x80000081, })
        self.assertEqual(compute('ADCS               R4,    R4,   R5    ROR 4 ',  {cf: 1, R4: 0xFFFFFFFF, R5: 0x0000010F, }), {
                         nf: 1, zf: 0, cf: 1, of: 0, R4: 0xF0000010, R5: 0x0000010F, })
        self.assertEqual(compute('ADCS               R4,    R4,   R5    RRX   ',  {cf: 1, R4: 0xFFFFFFFF, R5: 0x00000101, }), {
                         nf: 1, zf: 0, cf: 1, of: 0, R4: 0x80000080, R5: 0x00000101, })

        # §A8.8.3:                 ADC{S}{<c>}{<q>} {<Rd>,} <Rn>, <Rm>, <type> <Rs>
        self.assertEqual(compute('ADC                R4,    R6,   R4    LSL R5',  {
                                 cf: 0, R4: 0x00000001, R5: 0x00000004, R6: 0, }), {cf: 0,     R4: 0x00000010, R5: 0x00000004, R6: 0, })
        self.assertEqual(compute('ADC                R4,    R6,   R4    LSR R5',  {
                                 cf: 1, R4: 0x00000110, R5: 0x80000004, R6: 0, }), {cf: 1,     R4: 0x00000012, R5: 0x80000004, R6: 0, })
        self.assertEqual(compute('ADC                R4,    R6,   R4    ASR R5',  {
                                 cf: 0, R4: 0x80000010, R5: 0xF0000001, R6: 0, }), {cf: 0,     R4: 0xC0000008, R5: 0xF0000001, R6: 0, })
        self.assertEqual(compute('ADC                R4,    R6,   R4    ROR R5',  {
                                 cf: 1, R4: 0x000000FF, R5: 0x00000F04, R6: 0, }), {cf: 1,     R4: 0xF0000010, R5: 0x00000F04, R6: 0, })
        self.assertEqual(compute('ADCS               R4,    R6,   R4    LSL R5',  {cf: 0, R4: 0x00000001, R5: 0x00000004, R6: 0, }), {
                         nf: 0, zf: 0, cf: 0, of: 0, R4: 0x00000010, R5: 0x00000004, R6: 0, })
        self.assertEqual(compute('ADCS               R4,    R6,   R4    LSR R5',  {cf: 1, R4: 0x00000110, R5: 0x80000004, R6: 0, }), {
                         nf: 0, zf: 0, cf: 0, of: 0, R4: 0x00000012, R5: 0x80000004, R6: 0, })
        self.assertEqual(compute('ADCS               R4,    R6,   R4    ASR R5',  {cf: 0, R4: 0x80000010, R5: 0xF0000001, R6: 0, }), {
                         nf: 1, zf: 0, cf: 0, of: 0, R4: 0xC0000008, R5: 0xF0000001, R6: 0, })
        self.assertEqual(compute('ADCS               R4,    R6,   R4    ROR R5',  {cf: 1, R4: 0x000000FF, R5: 0x00000F04, R6: 0, }), {
                         nf: 1, zf: 0, cf: 0, of: 0, R4: 0xF0000010, R5: 0x00000F04, R6: 0, })

    def test_ADD(self):
        # §A8.8.{5,9}:             ADD{S}{<c>}{<q>} {<Rd>,} <Rn>, #<const>
        self.assertRaises(
            ValueError, compute, 'ADD          R4,   0x00000001 ')
        self.assertEqual(compute('ADD                R4,    R4,   0x00000001 ',   {
                                 R4: 0x00000000, }), {R4: 0x00000001, })
        self.assertEqual(compute('ADD                R4,    R4,   0x00000000 ',   {
                                 R4: 0x00000000, }), {R4: 0x00000000, })
        self.assertEqual(compute('ADD                PC,    R4,   0x00000001 ',   {
                                 R4: 0xFFFFFFFF, PC: 0x55555555, }), {R4: 0xFFFFFFFF, PC: 0x00000000, })
        self.assertEqual(compute('ADD                PC,    R4,   0x00000000 ',   {
                                 R4: 0xFFFFFFFF, PC: 0x55555555, }), {R4: 0xFFFFFFFF, PC: 0xFFFFFFFF, })
        self.assertEqual(compute('ADDS               R4,    R4,   0x80000000 ',   {R4: 0x80000000, }), {
                         nf: 0, zf: 1, cf: 1, of: 1, R4: 0x00000000, })
        self.assertEqual(compute('ADDS               R4,    R4,   0xFF000000 ',   {R4: 0x00FFFFFE, }), {
                         nf: 1, zf: 0, cf: 0, of: 0, R4: 0xFFFFFFFE, })
        self.assertEqual(compute('ADDS               PC,    R4,   0x00000000 ',   {
                                 R4: 0x00000000, PC: 0x55555555, }), {R4: 0x00000000, PC: 0x00000000, })
        self.assertEqual(compute('ADDS               PC,    R4,   0xFF000000 ',   {
                                 R4: 0x01000000, PC: 0x55555555, }), {R4: 0x01000000, PC: 0x00000000, })
        # SP special part
        self.assertEqual(compute('ADD                R4,    SP,   0x00000001 ',   {
                                 R4: 0x00000000, SP: 0x00000000, }), {R4: 0x00000001, SP: 0x00000000, })

        # §A8.8.{7,11}:            ADD{S}{<c>}{<q>} {<Rd>,} <Rn>, <Rm> {,<shift>}
        self.assertRaises(
            ValueError, compute, 'ADD          R4,   R5          ')
        self.assertEqual(compute('ADD                R4,    R4,   R5          ',  {
                                 R4: 0xFFFFFFFF, R5: 0x00000001, }), {R4: 0x00000000, R5: 0x00000001, })
        self.assertEqual(compute('ADD                R4,    R4,   R5    LSL 1 ',  {
                                 R4: 0x00000001, R5: 0x00000008, }), {R4: 0x00000011, R5: 0x00000008, })
        self.assertEqual(compute('ADD                R4,    R4,   R5    LSR 2 ',  {
                                 R4: 0x00000000, R5: 0x80000041, }), {R4: 0x20000010, R5: 0x80000041, })
        self.assertEqual(compute('ADD                R4,    R4,   R5    ASR 3 ',  {
                                 R4: 0x00000001, R5: 0x80000081, }), {R4: 0xF0000011, R5: 0x80000081, })
        self.assertEqual(compute('ADD                R4,    R4,   R5    ROR 4 ',  {
                                 R4: 0xFFFFFFFF, R5: 0x0000010F, }), {R4: 0xF000000F, R5: 0x0000010F, })
        self.assertEqual(compute('ADD                R4,    R4,   R5    RRX   ',  {
                                 cf: 1, R4: 0xFFFFFFFF, R5: 0x00000101, }), {cf: 1,     R4: 0x8000007F, R5: 0x00000101, })
        self.assertEqual(compute('ADDS               R4,    R4,   R5          ',  {R4: 0xFFFFFFFF, R5: 0x00000001, }), {
                         nf: 0, zf: 1, cf: 1, of: 0, R4: 0x00000000, R5: 0x00000001, })
        self.assertEqual(compute('ADDS               R4,    R4,   R5    LSL 1 ',  {R4: 0x00000001, R5: 0x00000008, }), {
                         nf: 0, zf: 0, cf: 0, of: 0, R4: 0x00000011, R5: 0x00000008, })
        self.assertEqual(compute('ADDS               R4,    R4,   R5    LSR 2 ',  {R4: 0x00000000, R5: 0x80000041, }), {
                         nf: 0, zf: 0, cf: 0, of: 0, R4: 0x20000010, R5: 0x80000041, })
        self.assertEqual(compute('ADDS               R4,    R4,   R5    ASR 3 ',  {R4: 0x00000001, R5: 0x80000081, }), {
                         nf: 1, zf: 0, cf: 0, of: 0, R4: 0xF0000011, R5: 0x80000081, })
        self.assertEqual(compute('ADDS               R4,    R4,   R5    ROR 4 ',  {R4: 0xFFFFFFFF, R5: 0x0000010F, }), {
                         nf: 1, zf: 0, cf: 1, of: 0, R4: 0xF000000F, R5: 0x0000010F, })
        self.assertEqual(compute('ADDS               R4,    R4,   R5    RRX   ',  {cf: 1, R4: 0xFFFFFFFF, R5: 0x00000101, }), {
                         nf: 1, zf: 0, cf: 1, of: 0, R4: 0x8000007F, R5: 0x00000101, })
        # SP special part
        self.assertEqual(compute('ADD                R4,    SP,   R4    LSR 1 ',  {
                                 R4: 0x00000002, SP: 0x00000000, }), {R4: 0x00000001, SP: 0x00000000, })

        # §A8.8.8:                 ADD{S}{<c>}{<q>} {<Rd>,} <Rn>, <Rm>, <type> <Rs>
        self.assertEqual(compute('ADD                R4,    R6,   R4    LSL R5',  {
                                 R4: 0x00000001, R5: 0x00000004, R6: 0, }), {R4: 0x00000010, R5: 0x00000004, R6: 0, })
        self.assertEqual(compute('ADD                R4,    R6,   R4    LSR R5',  {
                                 R4: 0x00000110, R5: 0x80000004, R6: 0, }), {R4: 0x00000011, R5: 0x80000004, R6: 0, })
        self.assertEqual(compute('ADD                R4,    R6,   R4    ASR R5',  {
                                 R4: 0x80000010, R5: 0xF0000001, R6: 0, }), {R4: 0xC0000008, R5: 0xF0000001, R6: 0, })
        self.assertEqual(compute('ADD                R4,    R6,   R4    ROR R5',  {
                                 R4: 0x000000FF, R5: 0x00000F04, R6: 0, }), {R4: 0xF000000F, R5: 0x00000F04, R6: 0, })
        self.assertEqual(compute('ADDS               R4,    R6,   R4    LSL R5',  {R4: 0x00000001, R5: 0x00000004, R6: 0, }), {
                         nf: 0, zf: 0, cf: 0, of: 0, R4: 0x00000010, R5: 0x00000004, R6: 0, })
        self.assertEqual(compute('ADDS               R4,    R6,   R4    LSR R5',  {R4: 0x00000110, R5: 0x80000004, R6: 0, }), {
                         nf: 0, zf: 0, cf: 0, of: 0, R4: 0x00000011, R5: 0x80000004, R6: 0, })
        self.assertEqual(compute('ADDS               R4,    R6,   R4    ASR R5',  {R4: 0x80000010, R5: 0xF0000001, R6: 0, }), {
                         nf: 1, zf: 0, cf: 0, of: 0, R4: 0xC0000008, R5: 0xF0000001, R6: 0, })
        self.assertEqual(compute('ADDS               R4,    R6,   R4    ROR R5',  {R4: 0x000000FF, R5: 0x00000F04, R6: 0, }), {
                         nf: 1, zf: 0, cf: 0, of: 0, R4: 0xF000000F, R5: 0x00000F04, R6: 0, })


        # Test against qemu
        self.assertEqual(compute('ADDS               R3,    R2,   R3 ', {R2: 0x1, R3: 0x1}),
                         { nf: 0, zf: 0, cf: 0, of: 0, R2: 0x00000001, R3: 0x00000002})
        self.assertEqual(compute('ADDS               R3,    R2,   R3 ', {R2: 0x1, R3: 0x7FFFFFFF}),
                         { nf: 1, zf: 0, cf: 0, of: 1, R2: 0x00000001, R3: 0x80000000})
        self.assertEqual(compute('ADDS               R3,    R2,   R3 ', {R2: 0x80000000, R3: 0x80000000}),
                         { nf: 0, zf: 1, cf: 1, of: 1, R2: 0x80000000, R3: 0x00000000})
        self.assertEqual(compute('ADDS               R3,    R2,   R3 ', {R2: 0x7FFFFFFF, R3:0x7FFFFFFF}),
                         { nf: 1, zf: 0, cf: 0, of: 1, R2: 0x7FFFFFFF, R3:0xFFFFFFFE})
        self.assertEqual(compute('ADDS               R3,    R2,   R3 ', {R2: 0, R3:0}),
                         { nf: 0, zf: 1, cf: 0, of: 0, R2: 0, R3:0})
        self.assertEqual(compute('ADDS               R3,    R2,   R3 ', {R2: 0xFFFFFFFF, R3:0xFFFFFFFF}),
                         { nf: 1, zf: 0, cf: 1, of: 0, R2: 0xFFFFFFFF, R3:0xFFFFFFFE})





    def test_ADR(self):
        # §A8.8.12:                ADR{<c>}{<q>} <Rd>, <label>    <==>    ADD{<c>}{<q>} <Rd>, PC, #<const>
        pass

    def test_AND(self):
        # §A8.8.13:                AND{S}{<c>}{<q>} {<Rd>,} <Rn>, #<const>
        self.assertRaises(
            ValueError, compute, 'AND          R4,   0x00000001 ')
        self.assertEqual(compute('AND                R4,    R4,   0x00000001 ',   {R4: 0xDEADBEEF, }), {R4: 0x00000001, })
        self.assertEqual(compute('AND                R4,    R4,   0x00000000 ',   {R4: 0x00000000, }), {R4: 0x00000000, })
        self.assertEqual(compute('AND                PC,    R4,   0x00000001 ',   {R4: 0xFFFFFFFF, PC: 0x55555555, }), {R4: 0xFFFFFFFF, PC: 0x00000001, })
        self.assertEqual(compute('AND                PC,    R4,   0x00000000 ',   {R4: 0xFFFFFFFF, PC: 0x55555555, }), {R4: 0xFFFFFFFF, PC: 0x00000000, })

        # §A8.8.14:                AND{S}{<c>}{<q>} {<Rd>,} <Rn>, <Rm> {,<shift>}
        self.assertRaises(
            ValueError, compute, 'AND          R4,   R5          ')
        self.assertEqual(compute('AND                R4,    R4,   R5          ',  {R4: 0xFFFFFFFE, R5: 0x00000001, }), {R4: 0x00000000, R5: 0x00000001, })
        self.assertEqual(compute('AND                R4,    R4,   R5    LSL 1 ',  {R4: 0x00000011, R5: 0x00000008, }), {R4: 0x00000010, R5: 0x00000008, })
        self.assertEqual(compute('AND                R4,    R4,   R5    LSR 2 ',  {R4: 0xFFFFFFFF, R5: 0x80000041, }), {R4: 0x20000010, R5: 0x80000041, })
        self.assertEqual(compute('AND                R4,    R4,   R5    ASR 3 ',  {R4: 0xF00000FF, R5: 0x80000081, }), {R4: 0xF0000010, R5: 0x80000081, })
        self.assertEqual(compute('AND                R4,    R4,   R5    ROR 4 ',  {R4: 0xFFFFFFFF, R5: 0x000000FF, }), {R4: 0xF000000F, R5: 0x000000FF, })
        self.assertEqual(compute('AND                R4,    R4,   R5    RRX   ',  {R4: 0xFFFFFFFF, R5: 0x00000101, }), {R4: ExprCompose(ExprInt(0x80, 31), cf_init), R5: 0x00000101, })

        # §A8.8.15:                AND{S}{<c>}{<q>} {<Rd>,} <Rn>, <Rm>, <type> <Rs>
        self.assertEqual(compute('AND                R4,    R6,   R4    LSL R5',  {R4: 0x00000001, R5: 0x00000004, R6: -1, }), {R4: 0x00000010, R5: 0x00000004, R6: 0xFFFFFFFF, })
        self.assertEqual(compute('AND                R4,    R6,   R4    LSR R5',  {R4: 0x00000110, R5: 0x80000004, R6: -1, }), {R4: 0x00000011, R5: 0x80000004, R6: 0xFFFFFFFF, })
        self.assertEqual(compute('AND                R4,    R6,   R4    ASR R5',  {R4: 0x80000010, R5: 0xF0000001, R6: -1, }), {R4: 0xC0000008, R5: 0xF0000001, R6: 0xFFFFFFFF, })
        self.assertEqual(compute('AND                R4,    R6,   R4    ROR R5',  {R4: 0x000000FF, R5: 0x00000F04, R6: -1, }), {R4: 0xF000000F, R5: 0x00000F04, R6: 0xFFFFFFFF, })

    def test_ASR(self):
        # §A8.8.16:                ASR{S}{<c>}{<q>} {<Rd>,} <Rm>, #<imm>    <==>    MOV{S}{<c>}{<q>} {<Rd>,} <Rm>, ASR #<n>
        pass

        # §A8.8.17:                ASR{S}{<c>}{<q>} {<Rd>,} <Rn>, <Rm>      <==>    MOV{S}{<c>}{<q>} {<Rd>,} <Rn>, ASR <Rm>
        pass

    def test_SUBS(self):
        # Test against qemu
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x2, R3: 0x1}),
                         { nf: 0, zf: 0, cf: 1, of: 0, R2: 0x00000002, R3: 0x1})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x1, R3: 0x2}),
                         { nf: 1, zf: 0, cf: 0, of: 0, R2: 0x00000001, R3: 0xFFFFFFFF})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x0, R3: 0xFFFFFFFF}),
                         { nf: 0, zf: 0, cf: 0, of: 0, R2: 0x00000000, R3: 0x1})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0xFFFFFFFF, R3: 0x0}),
                         { nf: 1, zf: 0, cf: 1, of: 0, R2: 0xFFFFFFFF, R3: 0xFFFFFFFF})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x1, R3: 0x7FFFFFFF}),
                         { nf: 1, zf: 0, cf: 0, of: 0, R2: 0x00000001, R3: 0x80000002})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x7FFFFFFF, R3: 0x1}),
                         { nf: 0, zf: 0, cf: 1, of: 0, R2: 0x7FFFFFFF, R3: 0x7FFFFFFE})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x80000000, R3: 0x80000001}),
                         { nf: 1, zf: 0, cf: 0, of: 0, R2: 0x80000000, R3: 0xFFFFFFFF})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x80000001, R3: 0x80000000}),
                         { nf: 0, zf: 0, cf: 1, of: 0, R2: 0x80000001, R3: 0x1})

    def test_CMP(self):
        # Test against qemu
        self.assertEqual(compute('CMP                R0,    R1 ', {R0: 0x11223344, R1: 0x88223344}),
                         { nf: 1, zf: 0, cf: 0, of: 1, R0: 0x11223344, R1: 0x88223344})

        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x2, R3: 0x1}),
                         { nf: 0, zf: 0, cf: 1, of: 0, R2: 0x00000002, R3: 0x1})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x1, R3: 0x2}),
                         { nf: 1, zf: 0, cf: 0, of: 0, R2: 0x00000001, R3: 0xFFFFFFFF})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x0, R3: 0xFFFFFFFF}),
                         { nf: 0, zf: 0, cf: 0, of: 0, R2: 0x00000000, R3: 0x1})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0xFFFFFFFF, R3: 0x0}),
                         { nf: 1, zf: 0, cf: 1, of: 0, R2: 0xFFFFFFFF, R3: 0xFFFFFFFF})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x1, R3: 0x7FFFFFFF}),
                         { nf: 1, zf: 0, cf: 0, of: 0, R2: 0x00000001, R3: 0x80000002})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x7FFFFFFF, R3: 0x1}),
                         { nf: 0, zf: 0, cf: 1, of: 0, R2: 0x7FFFFFFF, R3: 0x7FFFFFFE})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x80000000, R3: 0x80000001}),
                         { nf: 1, zf: 0, cf: 0, of: 0, R2: 0x80000000, R3: 0xFFFFFFFF})
        self.assertEqual(compute('SUBS               R3,    R2,   R3 ', {R2: 0x80000001, R3: 0x80000000}),
                         { nf: 0, zf: 0, cf: 1, of: 0, R2: 0x80000001, R3: 0x1})



    def test_ADDS(self):
        self.assertEqual(compute('ADDS   R2, R2, R3', {R2: 0x2, R3: 0x1}), {R2: 0x3, R3: 0x1, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x0})
        self.assertEqual(compute('ADDS   R2, R2, R3', {R2: 0x1, R3: 0x2}), {R2: 0x3, R3: 0x2, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x0})
        self.assertEqual(compute('ADDS   R2, R2, R3', {R2: 0x0, R3: 0xffffffffL}), {R2: 0xffffffffL, R3: 0xffffffffL, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('ADDS   R2, R2, R3', {R2: 0xffffffffL, R3: 0x0}), {R2: 0xffffffffL, R3: 0x0, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('ADDS   R2, R2, R3', {R2: 0x1, R3: 0x7fffffff}), {R2: 0x80000000L, R3: 0x7fffffff, of: 0x1, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('ADDS   R2, R2, R3', {R2: 0x7fffffff, R3: 0x1}), {R2: 0x80000000L, R3: 0x1, of: 0x1, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('ADDS   R2, R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {R2: 0x1, R3: 0x80000001L, of: 0x1, zf: 0x0, cf: 0x1, nf: 0x0})
        self.assertEqual(compute('ADDS   R2, R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {R2: 0x1, R3: 0x80000000L, of: 0x1, zf: 0x0, cf: 0x1, nf: 0x0})

    def test_ANDS(self):
        self.assertEqual(compute('ANDS   R2, R2, R3', {R2: 0x2, R3: 0x1}), {zf: 0x1, R2: 0x0, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('ANDS   R2, R2, R3', {R2: 0x1, R3: 0x2}), {zf: 0x1, R2: 0x0, nf: 0x0, R3: 0x2})
        self.assertEqual(compute('ANDS   R2, R2, R3', {R2: 0x0, R3: 0xffffffffL}), {zf: 0x1, R2: 0x0, nf: 0x0, R3: 0xffffffffL})
        self.assertEqual(compute('ANDS   R2, R2, R3', {R2: 0xffffffffL, R3: 0x0}), {zf: 0x1, R2: 0x0, nf: 0x0, R3: 0x0})
        self.assertEqual(compute('ANDS   R2, R2, R3', {R2: 0x1, R3: 0x7fffffff}), {zf: 0x0, R2: 0x1, nf: 0x0, R3: 0x7fffffff})
        self.assertEqual(compute('ANDS   R2, R2, R3', {R2: 0x7fffffff, R3: 0x1}), {zf: 0x0, R2: 0x1, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('ANDS   R2, R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {zf: 0x0, R2: 0x80000000L, nf: 0x1, R3: 0x80000001L})
        self.assertEqual(compute('ANDS   R2, R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {zf: 0x0, R2: 0x80000000L, nf: 0x1, R3: 0x80000000L})

    def test_BICS(self):
        self.assertEqual(compute('BICS   R2, R2, R3', {R2: 0x2, R3: 0x1}), {zf: 0x0, R2: 0x2, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('BICS   R2, R2, R3', {R2: 0x1, R3: 0x2}), {zf: 0x0, R2: 0x1, nf: 0x0, R3: 0x2})
        self.assertEqual(compute('BICS   R2, R2, R3', {R2: 0x0, R3: 0xffffffffL}), {zf: 0x1, R2: 0x0, nf: 0x0, R3: 0xffffffffL})
        self.assertEqual(compute('BICS   R2, R2, R3', {R2: 0xffffffffL, R3: 0x0}), {zf: 0x0, R2: 0xffffffffL, nf: 0x1, R3: 0x0})
        self.assertEqual(compute('BICS   R2, R2, R3', {R2: 0x1, R3: 0x7fffffff}), {zf: 0x1, R2: 0x0, nf: 0x0, R3: 0x7fffffff})
        self.assertEqual(compute('BICS   R2, R2, R3', {R2: 0x7fffffff, R3: 0x1}), {zf: 0x0, R2: 0x7ffffffe, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('BICS   R2, R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {zf: 0x1, R2: 0x0, nf: 0x0, R3: 0x80000001L})
        self.assertEqual(compute('BICS   R2, R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {zf: 0x0, R2: 0x1, nf: 0x0, R3: 0x80000000L})

    def test_CMN(self):
        self.assertEqual(compute('CMN   R2, R3', {R2: 0x2, R3: 0x1}), {R2: 0x2, R3: 0x1, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x0})
        self.assertEqual(compute('CMN   R2, R3', {R2: 0x1, R3: 0x2}), {R2: 0x1, R3: 0x2, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x0})
        self.assertEqual(compute('CMN   R2, R3', {R2: 0x0, R3: 0xffffffffL}), {R2: 0x0, R3: 0xffffffffL, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('CMN   R2, R3', {R2: 0xffffffffL, R3: 0x0}), {R2: 0xffffffffL, R3: 0x0, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('CMN   R2, R3', {R2: 0x1, R3: 0x7fffffff}), {R2: 0x1, R3: 0x7fffffff, of: 0x1, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('CMN   R2, R3', {R2: 0x7fffffff, R3: 0x1}), {R2: 0x7fffffff, R3: 0x1, of: 0x1, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('CMN   R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {R2: 0x80000000L, R3: 0x80000001L, of: 0x1, zf: 0x0, cf: 0x1, nf: 0x0})
        self.assertEqual(compute('CMN   R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {R2: 0x80000001L, R3: 0x80000000L, of: 0x1, zf: 0x0, cf: 0x1, nf: 0x0})

    def test_CMP(self):
        self.assertEqual(compute('CMP   R2, R3', {R2: 0x2, R3: 0x1}), {R2: 0x2, R3: 0x1, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x0})
        self.assertEqual(compute('CMP   R2, R3', {R2: 0x1, R3: 0x2}), {R2: 0x1, R3: 0x2, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('CMP   R2, R3', {R2: 0x0, R3: 0xffffffffL}), {R2: 0x0, R3: 0xffffffffL, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x0})
        self.assertEqual(compute('CMP   R2, R3', {R2: 0xffffffffL, R3: 0x0}), {R2: 0xffffffffL, R3: 0x0, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x1})
        self.assertEqual(compute('CMP   R2, R3', {R2: 0x1, R3: 0x7fffffff}), {R2: 0x1, R3: 0x7fffffff, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('CMP   R2, R3', {R2: 0x7fffffff, R3: 0x1}), {R2: 0x7fffffff, R3: 0x1, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x0})
        self.assertEqual(compute('CMP   R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {R2: 0x80000000L, R3: 0x80000001L, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('CMP   R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {R2: 0x80000001L, R3: 0x80000000L, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x0})

    def test_EORS(self):
        self.assertEqual(compute('EORS   R2, R2, R3', {R2: 0x2, R3: 0x1}), {zf: 0x0, R2: 0x3, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('EORS   R2, R2, R3', {R2: 0x1, R3: 0x2}), {zf: 0x0, R2: 0x3, nf: 0x0, R3: 0x2})
        self.assertEqual(compute('EORS   R2, R2, R3', {R2: 0x0, R3: 0xffffffffL}), {zf: 0x0, R2: 0xffffffffL, nf: 0x1, R3: 0xffffffffL})
        self.assertEqual(compute('EORS   R2, R2, R3', {R2: 0xffffffffL, R3: 0x0}), {zf: 0x0, R2: 0xffffffffL, nf: 0x1, R3: 0x0})
        self.assertEqual(compute('EORS   R2, R2, R3', {R2: 0x1, R3: 0x7fffffff}), {zf: 0x0, R2: 0x7ffffffe, nf: 0x0, R3: 0x7fffffff})
        self.assertEqual(compute('EORS   R2, R2, R3', {R2: 0x7fffffff, R3: 0x1}), {zf: 0x0, R2: 0x7ffffffe, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('EORS   R2, R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {zf: 0x0, R2: 0x1, nf: 0x0, R3: 0x80000001L})
        self.assertEqual(compute('EORS   R2, R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {zf: 0x0, R2: 0x1, nf: 0x0, R3: 0x80000000L})

    def test_MULS(self):
        self.assertEqual(compute('MULS   R2, R2, R3', {R2: 0x2, R3: 0x1}), {zf: 0x0, R2: 0x2, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('MULS   R2, R2, R3', {R2: 0x1, R3: 0x2}), {zf: 0x0, R2: 0x2, nf: 0x0, R3: 0x2})
        self.assertEqual(compute('MULS   R2, R2, R3', {R2: 0x0, R3: 0xffffffffL}), {zf: 0x1, R2: 0x0, nf: 0x0, R3: 0xffffffffL})
        self.assertEqual(compute('MULS   R2, R2, R3', {R2: 0xffffffffL, R3: 0x0}), {zf: 0x1, R2: 0x0, nf: 0x0, R3: 0x0})
        self.assertEqual(compute('MULS   R2, R2, R3', {R2: 0x1, R3: 0x7fffffff}), {zf: 0x0, R2: 0x7fffffff, nf: 0x0, R3: 0x7fffffff})
        self.assertEqual(compute('MULS   R2, R2, R3', {R2: 0x7fffffff, R3: 0x1}), {zf: 0x0, R2: 0x7fffffff, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('MULS   R2, R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {zf: 0x0, R2: 0x80000000L, nf: 0x1, R3: 0x80000001L})
        self.assertEqual(compute('MULS   R2, R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {zf: 0x0, R2: 0x80000000L, nf: 0x1, R3: 0x80000000L})

    def test_ORRS(self):
        self.assertEqual(compute('ORRS   R2, R2, R3', {R2: 0x2, R3: 0x1}), {zf: 0x0, R2: 0x3, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('ORRS   R2, R2, R3', {R2: 0x1, R3: 0x2}), {zf: 0x0, R2: 0x3, nf: 0x0, R3: 0x2})
        self.assertEqual(compute('ORRS   R2, R2, R3', {R2: 0x0, R3: 0xffffffffL}), {zf: 0x0, R2: 0xffffffffL, nf: 0x1, R3: 0xffffffffL})
        self.assertEqual(compute('ORRS   R2, R2, R3', {R2: 0xffffffffL, R3: 0x0}), {zf: 0x0, R2: 0xffffffffL, nf: 0x1, R3: 0x0})
        self.assertEqual(compute('ORRS   R2, R2, R3', {R2: 0x1, R3: 0x7fffffff}), {zf: 0x0, R2: 0x7fffffff, nf: 0x0, R3: 0x7fffffff})
        self.assertEqual(compute('ORRS   R2, R2, R3', {R2: 0x7fffffff, R3: 0x1}), {zf: 0x0, R2: 0x7fffffff, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('ORRS   R2, R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {zf: 0x0, R2: 0x80000001L, nf: 0x1, R3: 0x80000001L})
        self.assertEqual(compute('ORRS   R2, R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {zf: 0x0, R2: 0x80000001L, nf: 0x1, R3: 0x80000000L})

    def test_RSBS(self):
        self.assertEqual(compute('RSBS   R2, R2, R3', {R2: 0x2, R3: 0x1}), {R2: 0xffffffffL, R3: 0x1, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('RSBS   R2, R2, R3', {R2: 0x1, R3: 0x2}), {R2: 0x1, R3: 0x2, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x0})
        self.assertEqual(compute('RSBS   R2, R2, R3', {R2: 0x0, R3: 0xffffffffL}), {R2: 0xffffffffL, R3: 0xffffffffL, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x1})
        self.assertEqual(compute('RSBS   R2, R2, R3', {R2: 0xffffffffL, R3: 0x0}), {R2: 0x1, R3: 0x0, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x0})
        self.assertEqual(compute('RSBS   R2, R2, R3', {R2: 0x1, R3: 0x7fffffff}), {R2: 0x7ffffffe, R3: 0x7fffffff, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x0})
        self.assertEqual(compute('RSBS   R2, R2, R3', {R2: 0x7fffffff, R3: 0x1}), {R2: 0x80000002L, R3: 0x1, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('RSBS   R2, R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {R2: 0x1, R3: 0x80000001L, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x0})
        self.assertEqual(compute('RSBS   R2, R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {R2: 0xffffffffL, R3: 0x80000000L, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})

    def test_SUBS(self):
        self.assertEqual(compute('SUBS   R2, R2, R3', {R2: 0x2, R3: 0x1}), {R2: 0x1, R3: 0x1, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x0})
        self.assertEqual(compute('SUBS   R2, R2, R3', {R2: 0x1, R3: 0x2}), {R2: 0xffffffffL, R3: 0x2, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('SUBS   R2, R2, R3', {R2: 0x0, R3: 0xffffffffL}), {R2: 0x1, R3: 0xffffffffL, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x0})
        self.assertEqual(compute('SUBS   R2, R2, R3', {R2: 0xffffffffL, R3: 0x0}), {R2: 0xffffffffL, R3: 0x0, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x1})
        self.assertEqual(compute('SUBS   R2, R2, R3', {R2: 0x1, R3: 0x7fffffff}), {R2: 0x80000002L, R3: 0x7fffffff, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('SUBS   R2, R2, R3', {R2: 0x7fffffff, R3: 0x1}), {R2: 0x7ffffffe, R3: 0x1, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x0})
        self.assertEqual(compute('SUBS   R2, R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {R2: 0xffffffffL, R3: 0x80000001L, of: 0x0, zf: 0x0, cf: 0x0, nf: 0x1})
        self.assertEqual(compute('SUBS   R2, R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {R2: 0x1, R3: 0x80000000L, of: 0x0, zf: 0x0, cf: 0x1, nf: 0x0})

    def test_TEQ(self):
        self.assertEqual(compute('TEQ   R2, R3', {R2: 0x2, R3: 0x1}), {zf: 0x0, R2: 0x2, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('TEQ   R2, R3', {R2: 0x1, R3: 0x2}), {zf: 0x0, R2: 0x1, nf: 0x0, R3: 0x2})
        self.assertEqual(compute('TEQ   R2, R3', {R2: 0x0, R3: 0xffffffffL}), {zf: 0x0, R2: 0x0, nf: 0x1, R3: 0xffffffffL})
        self.assertEqual(compute('TEQ   R2, R3', {R2: 0xffffffffL, R3: 0x0}), {zf: 0x0, R2: 0xffffffffL, nf: 0x1, R3: 0x0})
        self.assertEqual(compute('TEQ   R2, R3', {R2: 0x1, R3: 0x7fffffff}), {zf: 0x0, R2: 0x1, nf: 0x0, R3: 0x7fffffff})
        self.assertEqual(compute('TEQ   R2, R3', {R2: 0x7fffffff, R3: 0x1}), {zf: 0x0, R2: 0x7fffffff, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('TEQ   R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {zf: 0x0, R2: 0x80000000L, nf: 0x0, R3: 0x80000001L})
        self.assertEqual(compute('TEQ   R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {zf: 0x0, R2: 0x80000001L, nf: 0x0, R3: 0x80000000L})

    def test_TST(self):
        self.assertEqual(compute('TST   R2, R3', {R2: 0x2, R3: 0x1}), {zf: 0x1, R2: 0x2, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('TST   R2, R3', {R2: 0x1, R3: 0x2}), {zf: 0x1, R2: 0x1, nf: 0x0, R3: 0x2})
        self.assertEqual(compute('TST   R2, R3', {R2: 0x0, R3: 0xffffffffL}), {zf: 0x1, R2: 0x0, nf: 0x0, R3: 0xffffffffL})
        self.assertEqual(compute('TST   R2, R3', {R2: 0xffffffffL, R3: 0x0}), {zf: 0x1, R2: 0xffffffffL, nf: 0x0, R3: 0x0})
        self.assertEqual(compute('TST   R2, R3', {R2: 0x1, R3: 0x7fffffff}), {zf: 0x0, R2: 0x1, nf: 0x0, R3: 0x7fffffff})
        self.assertEqual(compute('TST   R2, R3', {R2: 0x7fffffff, R3: 0x1}), {zf: 0x0, R2: 0x7fffffff, nf: 0x0, R3: 0x1})
        self.assertEqual(compute('TST   R2, R3', {R2: 0x80000000L, R3: 0x80000001L}), {zf: 0x0, R2: 0x80000000L, nf: 0x1, R3: 0x80000001L})
        self.assertEqual(compute('TST   R2, R3', {R2: 0x80000001L, R3: 0x80000000L}), {zf: 0x0, R2: 0x80000001L, nf: 0x1, R3: 0x80000000L})

    def test_UMULL(self):
        self.assertEqual(compute('UMULL R1, R2, R4, R5', {R4: 0x0L, R5: 0x0L}), {R1: 0x0L, R2: 0x0L, R4: 0x0L, R5: 0x0L})
        self.assertEqual(compute('UMULL R0, R1, R2, R3', {R2: 0x1L, R3: 0x80808080L}), {R0: 0x80808080L, R1: 0x0L, R2: 0x1L, R3: 0x80808080L})
        self.assertEqual(compute('UMULL R2, R3, R4, R5', {R4: 0x12345678L, R5: 0x87654321L}), {R2: 0x70b88d78L, R3: 0x09a0cd05L, R4: 0x12345678L, R5: 0x87654321L})
        self.assertEqual(compute('UMULL R2, R3, R4, R5', {R4: 0xffffffffL, R5: 0x00000002L}), {R2: 0xfffffffeL, R3: 0x00000001L, R4: 0xffffffffL, R5: 0x00000002L})

    def test_UMLAL(self):
        self.assertEqual(compute('UMLAL R1, R2, R4, R5', {R1: 0x0L, R2: 0x0L, R4: 0x1L, R5: 0x0L}), {R1: 0x0L, R2: 0x0L, R4: 0x1L, R5: 0x0L})
        self.assertEqual(compute('UMLAL R0, R1, R2, R3', {R0: 0x0L, R1: 0x0L, R2: 0x1L, R3: 0x80808080L}), {R0: 0x80808080L, R1: 0x0L, R2: 0x1L, R3: 0x80808080L})
        self.assertEqual(compute('UMLAL R2, R3, R4, R5', {R2: 0xffffffffL, R3: 0x0L, R4: 0x12345678L, R5: 0x87654321L}), {R2: 0x70b88d77L, R3: 0x09a0cd06L, R4: 0x12345678L, R5: 0x87654321L})
        self.assertEqual(compute('UMLAL R2, R3, R4, R5', {R2: 0xffffffffL, R3: 0x2L, R4: 0x12345678L, R5: 0x87654321L}), {R2: 0x70b88d77L, R3: 0x09a0cd08L, R4: 0x12345678L, R5: 0x87654321L})

    def test_SMULL(self):
        self.assertEqual(compute('SMULL R1, R2, R4, R5', {R4: 0x0L, R5: 0x0L}), {R1: 0x0L, R2: 0x0L, R4: 0x0L, R5: 0x0L})
        self.assertEqual(compute('SMULL R0, R1, R2, R3', {R2: 0x1L, R3: 0x80808080L}), {R0: 0x80808080L, R1: 0xffffffffL, R2: 0x1L, R3: 0x80808080L})
        self.assertEqual(compute('SMULL R0, R1, R2, R3', {R2: 0xffff0000L, R3: 0xffff0000L}), {R0: 0x0L, R1: 0x1L, R2: 0xffff0000L, R3: 0xffff0000L})
        self.assertEqual(compute('SMULL R2, R3, R4, R5', {R4: 0x12345678L, R5: 0x87654321L}), {R2: 0x70b88d78L, R3: 0xf76c768dL, R4: 0x12345678L, R5: 0x87654321L})
        self.assertEqual(compute('SMULL R2, R3, R4, R5', {R4: 0xffffffffL, R5: 0x00000002L}), {R2: 0xfffffffeL, R3: 0xffffffffL, R4: 0xffffffffL, R5: 0x00000002L})

    def test_SMLAL(self):
        self.assertEqual(compute('SMLAL R1, R2, R4, R5', {R1: 0x0L, R2: 0x0L, R4: 0x1L, R5: 0x0L}), {R1: 0x0L, R2: 0x0L, R4: 0x1L, R5: 0x0L})
        self.assertEqual(compute('SMLAL R0, R1, R2, R3', {R0: 0x0L, R1: 0x0L, R2: 0x1L, R3: 0x80808080L}), {R0: 0x80808080L, R1: 0xffffffffL, R2: 0x1L, R3: 0x80808080L})
        self.assertEqual(compute('SMLAL R2, R3, R4, R5', {R2: 0xffffffffL, R3: 0x0L, R4: 0x12345678L, R5: 0x87654321L}), {R2: 0x70b88d77L, R3: 0xf76c768eL, R4: 0x12345678L, R5: 0x87654321L})
        self.assertEqual(compute('SMLAL R2, R3, R4, R5', {R2: 0xffffffffL, R3: 0x00000002L, R4: 0x12345678L, R5: 0x87654321L}), {R2: 0x70b88d77L, R3: 0xf76c7690L, R4: 0x12345678L, R5: 0x87654321L})

if __name__ == '__main__':
    testsuite = unittest.TestLoader().loadTestsFromTestCase(TestARMSemantic)
    report = unittest.TextTestRunner(verbosity=2).run(testsuite)
    exit(len(report.errors + report.failures))
