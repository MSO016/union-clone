// Ghidra headless: decompila todas as funções do programa atual e grava em arquivo.
// Uso: analyzeHeadless <proj> <nome> -import <bin> -scriptPath <dir> -postScript DumpAll.java <saida> -deleteProject
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

import java.io.PrintWriter;

public class DumpAll extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		String outPath = args.length > 0
			? args[0]
			: "D:\\MSO\\Projects\\union-clone\\decomp\\native\\dump.c";

		DecompInterface decomp = new DecompInterface();
		decomp.openProgram(currentProgram);

		int n = 0;
		try (PrintWriter out = new PrintWriter(outPath, "UTF-8")) {
			out.println("// program: " + currentProgram.getName());
			FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
			while (it.hasNext() && !monitor.isCancelled()) {
				Function f = it.next();
				try {
					DecompileResults res = decomp.decompileFunction(f, 60, monitor);
					if (res != null && res.decompileCompleted() && res.getDecompiledFunction() != null) {
						out.println();
						out.println("// ==== " + f.getName() + " @ " + f.getEntryPoint() + " ====");
						out.println(res.getDecompiledFunction().getC());
						n++;
					} else {
						out.println();
						out.println("// ==== " + f.getName() + " @ " + f.getEntryPoint() + " ==== <falhou>");
					}
				} catch (Exception e) {
					out.println();
					out.println("// ==== " + f.getName() + " ==== <erro: " + e + ">");
				}
			}
			out.println();
			out.println("// total funcoes decompiladas: " + n);
		}
		decomp.dispose();
		println("OK, funcoes: " + n + " -> " + outPath);
	}
}
