import sys
from miasm2.jitter.csts import PAGE_READ, PAGE_WRITE, EXCEPT_ACCESS_VIOL
from miasm2.analysis.machine import Machine

def code_sentinelle(jitter):
    jitter.run = False
    jitter.pc = 0
    return True


machine = Machine("x86_32")
jitter = machine.jitter(sys.argv[1])

jitter.init_stack()

# nop
# mov eax, 0x42
# jmp 0x20

data = "90b842000000eb20".decode('hex')

# Will raise memory error at 0x40000028

error_raised = False
def raise_me(jitter):
    global error_raised
    error_raised = True
    assert jitter.pc == 0x40000028
    return False

jitter.add_exception_handler(EXCEPT_ACCESS_VIOL, raise_me)


run_addr = 0x40000000

jitter.vm.add_memory_page(run_addr, PAGE_READ | PAGE_WRITE, data)

jitter.jit.log_regs = True
jitter.jit.log_mn = True
jitter.push_uint32_t(0x1337beef)

jitter.add_breakpoint(0x1337beef, code_sentinelle)

jitter.init_run(run_addr)
jitter.continue_run()

assert error_raised is True
