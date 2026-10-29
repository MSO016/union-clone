# Ghidra headless (Jython): descompila TODAS as funcoes do programa atual.
# Uso: analyzeHeadless <projdir> <projname> -import <bin> -scriptPath <dir> -postScript DumpAll.py <saida> -deleteProject
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

args = getScriptArgs()
outfile = args[0] if len(args) > 0 else "D:\\MSO\\Projects\\union-clone\\decomp\\native\\dump.c"

out = open(outfile, "w")
prog = currentProgram
out.write("// program: %s\n" % prog.getName())

decomp = DecompInterface()
decomp.openProgram(prog)
monitor2 = ConsoleTaskMonitor()

fm = prog.getFunctionManager()
n = 0
for f in fm.getFunctions(True):
    try:
        res = decomp.decompileFunction(f, 60, monitor2)
        if res is not None and res.decompileCompleted():
            c = res.getDecompiledFunction().getC()
            out.write("\n// ==== %s @ %s ====\n" % (f.getName(), f.getEntryPoint()))
            out.write(c)
            n = n + 1
        else:
            out.write("\n// ==== %s @ %s ==== <falhou decompilar>\n" % (f.getName(), f.getEntryPoint()))
    except Exception as e:
        out.write("\n// ==== %s ==== <erro: %s>\n" % (f.getName(), e))
out.write("\n// total funcoes decompiladas: %d\n" % n)
out.close()
print("OK, funcoes: %d -> %s" % (n, outfile))
