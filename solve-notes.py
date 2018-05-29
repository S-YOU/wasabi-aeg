#!/usr/bin/env python2
## -*- coding: utf-8 -*-

from triton  import *
from pintool import *


isRead = None
Triton = getTritonContext()
crash_inputs = []
mc = None
mnode = None

def getMemoryString(addr):
    index = 0
    s = str()

    while getCurrentMemoryValue(addr+index):
        c = chr(getCurrentMemoryValue(addr+index))
        s += ("" if c not in string.printable else c)
        index += 1

    return s


def syscallsEntry(threadId, std):
    global isOpen
    global isRead
    global targetFd

    if getSyscallNumber(std) == SYSCALL64.READ:
        fd   = getSyscallArgument(std, 0)
        buff = getSyscallArgument(std, 1)
        size = getSyscallArgument(std, 2)
        if fd == 0:
            isRead = {'buff': buff, 'size': size}

    return

stdin_len = 0
def syscallsExit(threadId, std):
    global isOpen
    global isRead
    global targetFd
    global stdin_len

    ctxt = getTritonContext()

    if isRead is not None:
        size = isRead['size']
        buff = isRead['buff']
        print '\n[TT] Symbolizing stdin (buf=%#x, size=%d)' % (buff, size)
        for index in range(size):
            Triton.taintMemory(buff+index)
            print '\tread: %r' % chr(getCurrentMemoryValue(buff+index))
            crash_inputs.append(chr(getCurrentMemoryValue(buff+index)))
            # if stdin_len > 40 and stdin_len < 50:
            if True:
                ctxt.setConcreteMemoryValue(buff+index, getCurrentMemoryValue(buff+index))
                print "Symbolized input: ", ctxt.convertMemoryToSymbolicVariable(MemoryAccess(buff+index, CPUSIZE.BYTE))
            stdin_len += 1
        isRead = None

    return


def mycb(inst):
    global mc
    global mnode

    if inst.getAddress() & 0xfff == 0x00007ffff7a8c231 & 0xfff:
        if inst.isMemoryWrite() and Triton.getPathConstraintsAst().isSymbolized():
            mem, node = inst.getStoreAccess()[0]
            if (mem.getLeaAst() is not None) and mem.getLeaAst().isSymbolized():
                print inst
                mc = mem.getLeaAst()
                # mnode = node
                mnode = "DUMMEY"
                # print 'Path Constraint: %s' % str(pc)
                # print 'MemoryAccess LeaAst: %s' % str(mem.getLeaAst())
    return

def signals(threadId, sig):
    global Triton
    global crash_inputs
    global mc
    global mnode

    print "signals()"
    print sig

    found = False
    inputs = ['\0'] * 0x100
    astCtxt = Triton.getAstContext()

    try:
        if True:
            pc = Triton.getPathConstraintsAst()
            m = Triton.getModel(pc)
            if len(m) > 0:
                print '[TT] Model for Path Constraint:', m
                for k, v in m.items():
                    inputs[k] = chr(v.getValue())
            else:
                print '[TT] Model for Path Constraint: unsat'

        if mc is not None and mnode is not None:
            # m = Triton.getModel(astCtxt.equal(mc, astCtxt.bv(0x602060 + 0, CPUSIZE.QWORD_BIT)))
            m = Triton.getModel(astCtxt.equal(mc, astCtxt.bv(0x400ab0, CPUSIZE.QWORD_BIT))) # instant_win()
            # m = Triton.getModel(
            #         astCtxt.land([
            #             astCtxt.equal(mc, astCtxt.bv(0x602060 + 0, CPUSIZE.QWORD_BIT)),
            #             astCtxt.equal(mnode, astCtxt.bv(0x400ab0, CPUSIZE.QWORD_BIT)), # instant_win()
            #         ])
            #     )
            if len(m) > 0:
                found = True
                print '[TT] Model for Memory Access:', m
                for k, v in m.items():
                    inputs[k] = chr(v.getValue())
                    crash_inputs[k] = chr(v.getValue())
            else:
                print '[TT] Model for Memory Access: unsat'

        if found:
            print 'Found: '
            print inputs
            print '%r' % ''.join(inputs).strip('\0')
            print crash_inputs
            print '%r' % ''.join(crash_inputs)
        else:
            print 'not found ;('
    except Exception, e:
        print "Exception: ", e
        exit()

if __name__ == '__main__':

    # Define symbolic optimizations
    Triton.enableMode(MODE.ALIGNED_MEMORY, True) # **REQUIRED** (slowns, but nor SEGV and unsat)
    Triton.enableMode(MODE.ONLY_ON_SYMBOLIZED, True) # **REQUIRED**

    # Triton.enableMode(MODE.ONLY_ON_TAINTED, True)

    # Start JIT at the entry point
    startAnalysisFromEntry()

    # startAnalysisFromSymbol('main')

    # Add callback
    insertCall(mycb, INSERT_POINT.BEFORE)
    insertCall(signals, INSERT_POINT.SIGNALS) # wait for SIGSEGV

    insertCall(syscallsEntry, INSERT_POINT.SYSCALL_ENTRY)
    insertCall(syscallsExit,  INSERT_POINT.SYSCALL_EXIT)

    # Run Program
    runProgram()


"""
0x7fdf91bab231: mov byte ptr [rbp], al
[TT] Model for Memory Access: {42L: SymVar_42 = 0xB0, 43L: SymVar_43 = 0xA, 44L: SymVar_44 = 0x40, 45L: SymVar_45 = 0x0, 46L: SymVar_46 = 0x0, 47L: SymVar_47 = 0x0, 48L: SymVar_48 = 0x0, 49L: SymVar_49 = 0x0}
[TT] Model for Path Constraint: {0L: SymVar_0 = 0x6E, 2L: SymVar_2 = 0xF5, 3L: SymVar_3 = 0xF5, 4L: SymVar_4 = 0xF5, 5L: SymVar_5 = 0xA, 6L: SymVar_6 = 0xF5, 7L: SymVar_7 = 0xF5, 8L: SymVar_8 = 0xF5, 9L: SymVar_9 = 0xA, 10L: SymVar_10 = 0x6E, 12L: SymVar_12 = 0xF5, 13L: SymVar_13 = 0xF5, 14L: SymVar_14 = 0xF5, 15L: SymVar_15 = 0xF5, 16L: SymVar_16 = 0xA, 17L: SymVar_17 = 0xF5, 18L: SymVar_18 = 0xF5, 19L: SymVar_19 = 0xF5, 20L: SymVar_20 = 0xF5, 21L: SymVar_21 = 0xA, 22L: SymVar_22 = 0x75, 24L: SymVar_24 = 0x38, 25L: SymVar_25 = 0x3A, 26L: SymVar_26 = 0xF5, 27L: SymVar_27 = 0xF5, 28L: SymVar_28 = 0xF5, 29L: SymVar_29 = 0xF5, 30L: SymVar_30 = 0xF5, 31L: SymVar_31 = 0xF5, 32L: SymVar_32 = 0xF5, 33L: SymVar_33 = 0xF5, 34L: SymVar_34 = 0xF5, 35L: SymVar_35 = 0xF5, 36L: SymVar_36 = 0xF5, 37L: SymVar_37 = 0xF5, 38L: SymVar_38 = 0xF5, 39L: SymVar_39 = 0xF5, 40L: SymVar_40 = 0xF5, 41L: SymVar_41 = 0xF5, 42L: SymVar_42 = 0x80, 43L: SymVar_43 = 0x0, 44L: SymVar_44 = 0x0, 45L: SymVar_45 = 0x0, 46L: SymVar_46 = 0x0, 47L: SymVar_47 = 0x0, 48L: SymVar_48 = 0x0, 49L: SymVar_49 = 0x0, 50L: SymVar_50 = 0xF5, 51L: SymVar_51 = 0xF5, 52L: SymVar_52 = 0xF5, 53L: SymVar_53 = 0xF5, 54L: SymVar_54 = 0xF5, 55L: SymVar_55 = 0xF5, 56L: SymVar_56 = 0xF5, 57L: SymVar_57 = 0xF5, 58L: SymVar_58 = 0xA, 59L: SymVar_59 = 0xF5, 60L: SymVar_60 = 0xF5, 61L: SymVar_61 = 0xF5, 62L: SymVar_62 = 0xF5, 63L: SymVar_63 = 0xF5, 64L: SymVar_64 = 0xA, 65L: SymVar_65 = 0x75, 67L: SymVar_67 = 0x31, 68L: SymVar_68 = 0x3A, 69L: SymVar_69 = 0xF5, 70L: SymVar_70 = 0xF5, 71L: SymVar_71 = 0xF5, 72L: SymVar_72 = 0xF5, 73L: SymVar_73 = 0xF5, 74L: SymVar_74 = 0xA, 75L: SymVar_75 = 0xF5}
K_atc% gdb ./notes
gdb-peda$ notes < crash-inputs/notes-1
Stopped reason: SIGBUS
0x00007ffff7a8c231 in __GI__IO_getline_info () from /usr/lib/libc.so.6

[TT] Model for Path Constraint: {0L: SymVar_0 = 0x6E, 2L: SymVar_2 = 0xF5, 3L: SymVar_3 = 0xF5, 4L: SymVar_4 = 0xF5, 5L: SymVar_5 = 0xA, 6L: SymVar_6 = 0xF5, 7L: SymVar_7 = 0xF5, 8L: SymVar_8 = 0xF5, 9L: SymVar_9 = 0xA, 10L: SymVar_10 = 0x6E, 12L: SymVar_12 = 0xF5, 13L: SymVar_13 = 0xF5, 14L: SymVar_14 = 0xF5, 15L: SymVar_15 = 0xF5, 16L: SymVar_16 = 0xA, 17L: SymVar_17 = 0xF5, 18L: SymVar_18 = 0xF5, 19L: SymVar_19 = 0xF5, 20L: SymVar_20 = 0xF5, 21L: SymVar_21 = 0xA, 22L: SymVar_22 = 0x75, 24L: SymVar_24 = 0x38, 25L: SymVar_25 = 0x3A, 26L: SymVar_26 = 0xF5, 27L: SymVar_27 = 0xF5, 28L: SymVar_28 = 0xF5, 29L: SymVar_29 = 0xF5, 30L: SymVar_30 = 0xF5, 31L: SymVar_31 = 0xF5, 32L: SymVar_32 = 0xF5, 33L: SymVar_33 = 0xF5, 34L: SymVar_34 = 0xF5, 35L: SymVar_35 = 0xF5, 36L: SymVar_36 = 0xF5, 37L: SymVar_37 = 0xF5, 38L: SymVar_38 = 0xF5, 39L: SymVar_39 = 0xF5, 40L: SymVar_40 = 0xF5, 41L: SymVar_41 = 0xF5, 42L: SymVar_42 = 0x80, 43L: SymVar_43 = 0x0, 44L: SymVar_44 = 0x0, 45L: SymVar_45 = 0x0, 46L: SymVar_46 = 0x0, 47L: SymVar_47 = 0x0, 48L: SymVar_48 = 0x0, 49L: SymVar_49 = 0x0, 50L: SymVar_50 = 0xF5, 51L: SymVar_51 = 0xF5, 52L: SymVar_52 = 0xF5, 53L: SymVar_53 = 0xF5, 54L: SymVar_54 = 0xF5, 55L: SymVar_55 = 0xF5, 56L: SymVar_56 = 0xF5, 57L: SymVar_57 = 0xF5, 58L: SymVar_58 = 0xA, 59L: SymVar_59 = 0xF5, 60L: SymVar_60 = 0xF5, 61L: SymVar_61 = 0xF5, 62L: SymVar_62 = 0xF5, 63L: SymVar_63 = 0xF5, 64L: SymVar_64 = 0xA, 65L: SymVar_65 = 0x75, 67L: SymVar_67 = 0x31, 68L: SymVar_68 = 0x3A, 69L: SymVar_69 = 0xF5, 70L: SymVar_70 = 0xF5, 71L: SymVar_71 = 0xF5, 72L: SymVar_72 = 0xF5, 73L: SymVar_73 = 0xF5, 74L: SymVar_74 = 0xA, 75L: SymVar_75 = 0xF5}
[TT] Model for Memory Access: {42L: SymVar_42 = 0xB0, 43L: SymVar_43 = 0xA, 44L: SymVar_44 = 0x40, 45L: SymVar_45 = 0x0, 46L: SymVar_46 = 0x0, 47L: SymVar_47 = 0x0, 48L: SymVar_48 = 0x0, 49L: SymVar_49 = 0x0}
Found: 
['n', 0, '\xf5', '\xf5', '\xf5', '\n', '\xf5', '\xf5', '\xf5', '\n', 'n', 0, '\xf5', '\xf5', '\xf5', '\xf5', '\n', '\xf5', '\xf5', '\xf5', '\xf5', '\n', 'u', 0, '8', ':', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xb0', '\n', '@', '\x00', '\x00', '\x00', '\x00', '\x00', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\n', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\n', 'u', 0, '1', ':', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\n', '\xf5', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

[TT] Model for Path Constraint: {0L: SymVar_0 = 0x6E, 2L: SymVar_2 = 0xF5, 3L: SymVar_3 = 0xF5, 4L: SymVar_4 = 0xF5, 5L: SymVar_5 = 0xA, 6L: SymVar_6 = 0xF5, 7L: SymVar_7 = 0xF5, 8L: SymVar_8 = 0xF5, 9L: SymVar_9 = 0xA, 10L: SymVar_10 = 0x6E, 12L: SymVar_12 = 0xF5, 13L: SymVar_13 = 0xF5, 14L: SymVar_14 = 0xF5, 15L: SymVar_15 = 0xF5, 16L: SymVar_16 = 0xA, 17L: SymVar_17 = 0xF5, 18L: SymVar_18 = 0xF5, 19L: SymVar_19 = 0xF5, 20L: SymVar_20 = 0xF5, 21L: SymVar_21 = 0xA, 22L: SymVar_22 = 0x75, 24L: SymVar_24 = 0x38, 25L: SymVar_25 = 0x3A, 26L: SymVar_26 = 0xF5, 27L: SymVar_27 = 0xF5, 28L: SymVar_28 = 0xF5, 29L: SymVar_29 = 0xF5, 30L: SymVar_30 = 0xF5, 31L: SymVar_31 = 0xF5, 32L: SymVar_32 = 0xF5, 33L: SymVar_33 = 0xF5, 34L: SymVar_34 = 0xF5, 35L: SymVar_35 = 0xF5, 36L: SymVar_36 = 0xF5, 37L: SymVar_37 = 0xF5, 38L: SymVar_38 = 0xF5, 39L: SymVar_39 = 0xF5, 40L: SymVar_40 = 0xF5, 41L: SymVar_41 = 0xF5, 42L: SymVar_42 = 0x80, 43L: SymVar_43 = 0x0, 44L: SymVar_44 = 0x0, 45L: SymVar_45 = 0x0, 46L: SymVar_46 = 0x0, 47L: SymVar_47 = 0x0, 48L: SymVar_48 = 0x0, 49L: SymVar_49 = 0x0, 50L: SymVar_50 = 0xF5, 51L: SymVar_51 = 0xF5, 52L: SymVar_52 = 0xF5, 53L: SymVar_53 = 0xF5, 54L: SymVar_54 = 0xF5, 55L: SymVar_55 = 0xF5, 56L: SymVar_56 = 0xF5, 57L: SymVar_57 = 0xF5, 58L: SymVar_58 = 0xA, 59L: SymVar_59 = 0xF5, 60L: SymVar_60 = 0xF5, 61L: SymVar_61 = 0xF5, 62L: SymVar_62 = 0xF5, 63L: SymVar_63 = 0xF5, 64L: SymVar_64 = 0xA, 65L: SymVar_65 = 0x75, 67L: SymVar_67 = 0x31, 68L: SymVar_68 = 0x3A, 69L: SymVar_69 = 0xF5, 70L: SymVar_70 = 0xF5, 71L: SymVar_71 = 0xF5, 72L: SymVar_72 = 0xF5, 73L: SymVar_73 = 0xF5, 74L: SymVar_74 = 0xA, 75L: SymVar_75 = 0xF5}
[TT] Model for Memory Access: {42L: SymVar_42 = 0xB0, 43L: SymVar_43 = 0xA, 44L: SymVar_44 = 0x40, 45L: SymVar_45 = 0x0, 46L: SymVar_46 = 0x0, 47L: SymVar_47 = 0x0, 48L: SymVar_48 = 0x0, 49L: SymVar_49 = 0x0}
Found: 
['n', '\x00', '\xf5', '\xf5', '\xf5', '\n', '\xf5', '\xf5', '\xf5', '\n', 'n', '\x00', '\xf5', '\xf5', '\xf5', '\xf5', '\n', '\xf5', '\xf5', '\xf5', '\xf5', '\n', 'u', '\x00', '8', ':', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xb0', '\n', '@', '\x00', '\x00', '\x00', '\x00', '\x00', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\n', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\n', 'u', '\x00', '1', ':', '\xf5', '\xf5', '\xf5', '\xf5', '\xf5', '\n', '\xf5', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00']
'n\x00\xf5\xf5\xf5\n\xf5\xf5\xf5\nn\x00\xf5\xf5\xf5\xf5\n\xf5\xf5\xf5\xf5\nu\x008:\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xb0\n@\x00\x00\x00\x00\x00\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\n\xf5\xf5\xf5\xf5\xf5\nu\x001:\xf5\xf5\xf5\xf5\xf5\n\xf5'
['n', '\n', 't', 'i', 't', '\n', 'c', 'o', 'n', '\n', 'n', '\n', 't', 'i', 't', '!', '\n', 'c', 'o', 'n', '!', '\n', 'u', '\n', '1', '\n', 'A', 'A', 'A', '%', 'A', 'A', 's', 'A', 'A', 'B', 'A', 'A', '$', 'A', 'A', 'n', '\xb0', '\n', '@', '\x00', '\x00', '\x00', '\x00', '\x00', '(', 'A', 'A', 'D', 'A', 'A', ';', 'A', '\n', 'c', 'o', 'n', '!', '!', '\n', 'u', '\n', '2', '\n', 't', 'i', 't', '!', '!', '\n', 'c']
'n\ntit\ncon\nn\ntit!\ncon!\nu\n1\nAAA%AAsAABAA$AAn\xb0\n@\x00\x00\x00\x00\x00(AADAA;A\ncon!!\nu\n2\ntit!!\nc'

"""