# -*- coding: utf-8 -*-
import sys
from siga_runner import run_option2, run_option5

def main():
    if len(sys.argv) < 2:
        print("Uso: python tasks.py [option2|option5] [periodo_992]")
        raise SystemExit(1)

    opt = sys.argv[1]
    if opt == "option2":
        print(run_option2())
    elif opt == "option5":
        if len(sys.argv) < 3:
            print("Falta periodo_992. Ej: python tasks.py option5 2025011112")
            raise SystemExit(1)
        print(run_option5(int(sys.argv[2])))
    else:
        print("Opción inválida.")
        raise SystemExit(1)

if __name__ == "__main__":
    main()