# El corredor de código

El corredor ejecuta el código de un alumno con Qiskit y Qiskit Aer y devuelve lo
que imprimió y el resultado de los casos de un ejercicio, con el formato de
[`qgcheck.grade`](exercises.md#corregir-código). Es una imagen de contenedor con
un servidor HTTP. No depende del anfitrión: el mismo contrato vale en Cloudflare
Containers y en Docker. Es el `POST /run` que llama el editor de las lecciones,
con aislamiento para exponerlo en red; `tools/serve.py` lo responde en tu equipo
sin él.

## Contrato

`POST /run` con un JSON:

| Campo      | Tipo  | Significado                                                                            |
| ---------- | ----- | -------------------------------------------------------------------------------------- |
| `code`     | texto | El código del alumno, hasta 20 000 bytes.                                              |
| `mode`     | texto | `run` (por defecto) ejecuta el código. `check` además lo prueba con el ejercicio.      |
| `exercise` | texto | `lección/ejercicio`, por ejemplo `p1-quickstart/ghz`. Obligatorio con `mode: "check"`. |

Responde 200 con:

```json
{
  "passed": false,
  "stdout": "",
  "error": null,
  "tests": [
    {
      "name": "n = 2, 3 y 4",
      "visible": true,
      "passed": false,
      "message": "Con n = 2 salen ['00'], y deberían salir solo 00 y 11."
    },
    {
      "name": "caso oculto 1",
      "visible": false,
      "passed": false,
      "message": "Con otros tamaños de n no salen solo 00…0 y 11…1."
    }
  ],
  "ms": 2438,
  "killed": null,
  "peak_mb": 169
}
```

- `passed` es verdadero si `error` es `null` y, con `check`, hay al menos un
  caso y todos pasan.
- `stdout` junta la salida estándar y la de errores, en el orden en que se
  escribieron. Con `check` es la del código del alumno al cargarse, una vez, y
  la que imprimen sus funciones.
- `error` es el error del código del alumno, con su línea, o el motivo por el
  que el corredor lo detuvo. Con un error, `tests` está vacío.
- `tests` está vacío con `mode: "run"`. Un caso oculto se llama `caso oculto N`.
- `killed` es `time`, `memory`, `disk` u `output` cuando el corredor mató el
  trabajo por ese límite, y `null` si no.
- `ms` es el tiempo del trabajo dentro del corredor. `peak_mb` es la mayor suma
  de memoria residente de los procesos del trabajo.

Otras respuestas llevan `{"error": "..."}`: 400 si la petición no es válida, 404
si el ejercicio no existe, 413 si el código pasa de 20 000 bytes o el cuerpo de
121 024 (seis veces el código, que es lo que ocupa un carácter de control en
JSON, más la envoltura) y 503 si no queda una ranura libre. `GET /health`
responde 200.

## Límites

| Límite                | Valor              | Cómo se aplica                                                               |
| --------------------- | ------------------ | ---------------------------------------------------------------------------- |
| Tiempo                | 10 s               | `sandbox.py` mata el grupo de procesos y todo proceso del mismo uid.         |
| Memoria               | 512 MB             | `sandbox.py` suma la memoria residente cada 20 ms y mata al pasar el tope.   |
| Directorio de trabajo | 64 MB              | `sandbox.py` mide el disco cada 100 ms; un archivo no pasa de 16 MB.         |
| Procesos e hilos      | 64                 | `RLIMIT_NPROC` sobre el uid de la ranura.                                    |
| Salida                | 64 KiB             | `sandbox.py` mata el trabajo al pasarse.                                     |
| Red                   | solo `AF_UNIX`     | Un filtro seccomp de `launcher.py` niega `socket` de cualquier otra familia. |
| Escritura             | solo su directorio | Un uid sin privilegios; `/scratch`, `/tmp` y `/app` son de root.             |

Un trabajo corre con el uid de su ranura, sin capacidades y con `no_new_privs`.
Al terminar se matan los procesos de ese uid y se borran su directorio y lo que
dejó en `/scratch`, `/tmp`, `/var/tmp` y `/dev/shm`. El servidor ejecuta tantos
trabajos a la vez como ranuras tiene (`QG_JOBS`, por defecto 1); el ciclo de las
ranuras está en [architecture.md](architecture.md#runner). Los demás valores se
cambian con `QG_WALL_S`, `QG_MEM_MB` y `QG_SCRATCH_MB`.

Con `mode: "run"` el código del alumno corre en el proceso del trabajo. Con
`mode: "check"` hay tres tipos de proceso del mismo uid. `grader.job` es el
comprobador: importa `check.py` y corre sus casos con `qgcheck`. Su hijo
`grader.broker` es un intermediario que no ejecuta código del alumno: por cada
acceso a `learner.<nombre>` que hace un caso (qué nombres hay, el valor de uno o
su llamada) hace un `fork`, y el hijo cierra todos los descriptores salvo un
pipe propio de esa petición, ejecuta el código del alumno desde cero, responde y
escribe un único mensaje por ese pipe. Entre procesos solo viajan datos:
números, textos, listas, arreglos de NumPy y circuitos en QPY. El comprobador y
el intermediario se declaran no volcables, así que el alumno no lee ni escribe
su memoria ni abre sus descriptores. El alumno decide el valor que devuelve cada
petición, lo calcule su función o no, y los casos juzgan ese valor; no puede
adelantar respuestas ni tocar el resultado de los casos. Como cada petición
vuelve a ejecutar el código, el estado de nivel superior no pasa de una a otra y
su salida solo se muestra en la primera. El alumno sí puede leer `check.py`: el
corredor protege el anfitrión y la corrección, no la clave de respuestas.

## Archivos

| Archivo                            | Función                                                                          |
| ---------------------------------- | -------------------------------------------------------------------------------- |
| `runner/server.py`                 | El servidor HTTP y la validación de la petición.                                 |
| `runner/sandbox.py`                | Lanza el trabajo y vigila tiempo, memoria, disco y salida.                       |
| `runner/launcher.py`               | Fija los rlimits, baja de uid e instala el filtro seccomp antes del `exec`.      |
| `runner/grader/`                   | El comprobador (`job.py`), el intermediario del alumno y su formato de mensajes. |
| `qgcheck/`                         | El corrector de [exercises.md](exercises.md). La imagen lo copia sin cambios.    |
| `runner/Dockerfile`                | La imagen. Sus versiones salen del grupo `runner` de `uv.lock`.                  |
| `runner/local.py`                  | Construye la imagen y la ejecuta con Docker y las banderas de aislamiento.       |
| `runner/bench.py`                  | Mide la latencia fría y templada.                                                |
| `runner/worker/`                   | El Worker de Cloudflare que arranca la imagen como Container.                    |
| `exercises/<lección>/<ejercicio>/` | La imagen solo lleva `check.py` de cada uno.                                     |

## Ejecutarlo con Docker

```sh
python runner/local.py serve
```

Construye la imagen `qg-runner` si hace falta (`python runner/local.py build`),
la arranca y escribe su URL. Usa gVisor (`runsc`) si Docker lo tiene registrado
y `runc` si no; `--runtime` lo fuerza. El contenedor va en una red interna de
Docker, sin salida a internet, con el sistema de archivos de solo lectura y sin
más capacidades que `SETUID`, `SETGID`, `KILL`, `CHOWN`, `FOWNER` y
`DAC_OVERRIDE`. Se alcanza por su IP, lo que funciona en Linux.

```sh
curl -s $URL/run -d '{"code": "print(2 + 2)"}'
```

## Pruebas y medidas

```sh
mise run runner
python runner/bench.py --runs 50
```

`tests/runner_test.py` construye la imagen, la arranca y habla con `/run` por
HTTP. Cubre el contrato, que el resultado de cada ejercicio sea el de
`qgcheck.grade`, los intentos de falsear un resultado y cada límite. Se salta si
Docker no responde.

## Cloudflare Containers

`runner/worker/` es un Worker con una clase `Runner` que extiende `Container`
(`@cloudflare/containers`) y reparte las peticiones entre tres instancias. Si la
instancia elegida responde 503, repite la petición una vez. Los Containers
requieren el plan Workers Paid. La instancia no tiene salida a internet
(`enableInternet = false`) y se apaga a los 5 minutos sin peticiones.

```sh
cd runner/worker
bun install
bunx cf deploy --dry-run   # construye la imagen y el Worker, no sube nada
bunx cf deploy
```

`cf deploy` necesita Docker en el `PATH`.
