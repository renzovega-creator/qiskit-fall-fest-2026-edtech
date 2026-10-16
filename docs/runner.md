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

| Archivo                              | Función                                                                          |
| ------------------------------------ | -------------------------------------------------------------------------------- |
| `runner/server.py`                   | El servidor HTTP y la validación de la petición.                                 |
| `runner/sandbox.py`                  | Lanza el trabajo y vigila tiempo, memoria, disco y salida.                       |
| `runner/launcher.py`                 | Fija los rlimits, baja de uid e instala el filtro seccomp antes del `exec`.      |
| `runner/grader/`                     | El comprobador (`job.py`), el intermediario del alumno y su formato de mensajes. |
| `qgcheck/`                           | El corrector de [exercises.md](exercises.md). La imagen lo copia sin cambios.    |
| `runner/Dockerfile`                  | La imagen. Sus versiones salen del grupo `runner` de `uv.lock`.                  |
| `runner/local.py`                    | Construye la imagen y la ejecuta con Docker y las banderas de aislamiento.       |
| `runner/bench.py`                    | Mide la latencia fría y templada.                                                |
| `runner/worker/`                     | El Worker de Cloudflare: sirve `site/` y arranca la imagen como Container.       |
| `runner/worker/cloudflare.config.ts` | El Worker, el Container, los Durable Objects, las variables y las rutas.         |
| `runner/worker/wrangler.config.ts`   | El directorio de `site/` que el Worker publica como archivos estáticos.          |
| `runner/worker/src/routes.ts`        | Las rutas que entran al Worker antes que a los archivos.                         |
| `runner/worker/src/index.ts`         | Las comprobaciones de [Protección del Worker](#protección-del-worker).           |
| `runner/worker/src/meters.ts`        | Los Durable Objects `RateLimiter` y `Budget`.                                    |
| `runner/worker/src/session.ts`       | La cookie de sesión y la llamada a `siteverify`.                                 |
| `runner/worker/src/log.ts`           | La única línea que el Worker escribe en su registro.                             |
| `runner/worker/test/`                | Las pruebas del Worker con un contenedor falso.                                  |
| `exercises/<lección>/<ejercicio>/`   | La imagen solo lleva `check.py` de cada uno.                                     |

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

```sh
mise run worker
```

Las pruebas del Worker (`runner/worker/test/`) arrancan el Worker real en el
runtime local de Cloudflare (Miniflare), con `site/` como archivos estáticos y
las mismas rutas de entrada que el despliegue, y con un contenedor falso que
anota cada llamada. No necesitan Docker ni cuenta. Comprueban que `GET /` sirve
`index.html`, que `POST /run` devuelve el JSON del corredor y cada límite de
[Protección del Worker](#protección-del-worker) por su respuesta y, con el
contenedor falso, que una petición rechazada no lo alcanza. Dos pruebas llaman
al `siteverify` real con las claves de prueba y se saltan si no hay red.

## Cloudflare Containers

`runner/worker/` es un solo Worker que sirve el sitio y el corredor en el mismo
origen: el editor llama a `/run` y la cookie de sesión es `SameSite=Strict`.

- Los archivos de `site/` son sus archivos estáticos. El directorio lo fija
  [`wrangler.config.ts`](../runner/worker/wrangler.config.ts).
- `/run`, `/health`, `/auth/*` y `/api/*` entran al código del Worker antes que
  a los archivos (`run_worker_first`). La lista está en
  [`src/routes.ts`](../runner/worker/src/routes.ts), que usan también el
  despliegue y las pruebas. Cualquier otra ruta la responde el servicio de
  archivos sin ejecutar el Worker, y una ruta que no es un archivo responde 404.
  Hoy el Worker responde 404 en `/auth/*` y `/api/*`.
- Una clase `Runner` que extiende `Container` (`@cloudflare/containers`) reparte
  las peticiones de `/run` entre tres instancias. Si la instancia elegida
  responde 503, repite la petición una vez. La instancia no tiene salida a
  internet (`enableInternet = false`) y se apaga a los 5 minutos sin peticiones.

Un solo `cf deploy` construye la imagen, empaqueta el Worker y sube `site/` como
una versión. Para publicar un cambio de las lecciones hay que volver a
desplegar.

### Lo que fija el operador

- El plan Workers Paid, que los Containers requieren.
- Docker en el `PATH` y accesible para quien despliega: `cf deploy` construye la
  imagen en su equipo.
- Un widget de Cloudflare Turnstile cuyos nombres de host incluyan el del sitio.
  Su clave del sitio es pública y va en `TURNSTILE_SITE_KEY` de
  [`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts). Su secreto es
  `TURNSTILE_SECRET` y no se escribe en el repositorio. Con `TURNSTILE_SITE_KEY`
  vacía, un `POST /run` sin sesión responde 500 `internal_error` y registra la
  variable que falta.
- Para servir el sitio en un dominio propio, el campo `domains` de `worker` en
  `cloudflare.config.ts`. Hoy no lo declara.

```sh
cd runner/worker
bun install
bunx cf deploy --dry-run   # construye la imagen y el Worker, no sube nada
umask 077
read -rs -p 'Secreto de Turnstile: ' secret && printf 'TURNSTILE_SECRET=%s\n' "$secret" > "$TMPDIR/secrets.env"
bunx cf deploy --secrets-file "$TMPDIR/secrets.env"
rm "$TMPDIR/secrets.env"
```

`--secrets-file` sube `TURNSTILE_SECRET` con la versión (JSON o `.env`).

## Protección del Worker

El Worker comprueba cada `POST /run` antes de arrancar el contenedor. Las
comprobaciones van en este orden, y la primera que falla responde sin que el
contenedor reciba nada:

1. El límite por IP.
2. El tamaño del cuerpo y del código.
3. El presupuesto del mes.
4. Turnstile, si la petición no trae una sesión válida.

Una negativa lleva `{"error": "...", "reason": "..."}`. El editor muestra el
texto de `error` tal cual. Todos los valores salen de `env` en
[`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts); cambiarlos es
editar ese archivo y desplegar. Un valor ausente o que no es un número positivo
hace que el Worker responda 500 con `internal_error` y registre qué variable
falló.

`GET /health` lo responde el Worker con 200 sin tocar un contenedor, para que
una petición sin límite no pueda mantener una instancia encendida.

### Límite por IP

| Variable          | Valor | Significa                                   |
| ----------------- | ----- | ------------------------------------------- |
| `RATE_PER_MINUTE` | 30    | Peticiones por IP en cada minuto del reloj. |
| `RATE_PER_DAY`    | 1000  | Peticiones por IP en cada día UTC.          |

Cuenta toda petición a `/run` desde que llega, también las que luego se rechazan
por tamaño o por Turnstile. Pasado el límite responde 429 con `Retry-After` en
segundos y `reason` `rate_minute` o `rate_day`. El alumno ve:

- «Estás ejecutando demasiado seguido. Espera 12 s y vuelve a intentarlo.»
- «Llegaste al límite de ejecuciones de hoy. Puedes volver a ejecutar en 5 h.»

La IP es `CF-Connecting-IP`. Sin esa cabecera (en local) todas las peticiones
comparten un solo contador. Una clase entera detrás de una misma IP comparte el
límite.

El contador de una IP vive en un Durable Object `RateLimiter` que se nombra con
un HMAC de la IP y del día. La clave del HMAC sale de `TURNSTILE_SECRET`, así
que el nombre no se puede volver a una IP sin ese secreto. El objeto guarda dos
contadores y borra su estado cuando termina el día.

### Tamaño del código

| Variable         | Valor  | Significa                     |
| ---------------- | ------ | ----------------------------- |
| `MAX_CODE_BYTES` | 20 000 | Bytes UTF-8 del campo `code`. |

Un código mayor responde 413 con `reason` `too_large` y el alumno ve «El código
ocupa 20001 bytes y el máximo son 20000.». Un cuerpo mayor que seis veces el
máximo más 1024 bytes responde 413 sin leerse entero. Un cuerpo que no es JSON o
no trae `code` como texto responde 400 (`bad_request`). El contenedor repite la
comprobación con `MAX_CODE` de `qgcheck/runner.py`; para cambiar el tope hay que
cambiar los dos.

### Presupuesto mensual

| Variable                | Valor     | Significa                                                           |
| ----------------------- | --------- | ------------------------------------------------------------------- |
| `MONTHLY_BUDGET_USD`    | 20        | Gasto estimado del mes UTC que no se supera.                        |
| `USD_PER_BUSY_SECOND`   | 0.0000075 | Coste de un segundo con una instancia ocupada.                      |
| `RESERVED_BUSY_SECONDS` | 30        | Segundos que una ejecución aparta del presupuesto antes de empezar. |

Antes de arrancar el contenedor, el Worker aparta en el Durable Object `Budget`
`RESERVED_BUSY_SECONDS` por `USD_PER_BUSY_SECOND`. Si con esa reserva el total
del mes pasaría de `MONTHLY_BUDGET_USD`, no ejecuta: responde 503 con
`Retry-After` hasta el día 1 del mes siguiente y `reason` `budget`. Comprobar y
apartar es una sola operación del objeto, así que varias peticiones simultáneas
no pueden apartar a la vez lo que solo cabe una vez. Al terminar, cambia la
reserva por el coste medido: el tiempo que esperó al contenedor (el arranque
incluido), en pasos de 10 ms y con un mínimo de un paso, por
`USD_PER_BUSY_SECOND`, y nunca más de lo apartado. Una petición que se rechaza
después de apartar (por Turnstile) devuelve la reserva entera. El total del mes
anterior se descarta. El alumno ve «El corredor alcanzó su presupuesto de este
mes y no ejecuta más código hasta que empiece el siguiente. Los cuadernos de
marimo siguen funcionando en tu equipo.»

`RESERVED_BUSY_SECONDS` es un tope y no una estimación. Cubre los 10 s de
trabajo de [Límites](#límites), el arranque de una instancia y el reintento tras
un 503. Si la ejecución, con su reintento, llega a ese tiempo, el Worker detiene
la instancia que aún no había respondido, cobra exactamente lo apartado y
responde 504 con `reason` `run_too_long`. Una instancia que respondió 503
atiende el trabajo de otro alumno y no se detiene. El alumno ve «La ejecución
tardó más de lo que el corredor permite y se detuvo. Revisa si el código tiene
un bucle sin fin.» Como cada ejecución cuesta como mucho lo que apartó y solo se
aparta si cabe, el gasto medido del mes no pasa de `MONTHLY_BUDGET_USD`. Si el
Worker se interrumpe entre apartar y terminar, o falla el almacenamiento al
terminar (se registra con `where: "settle"` y la respuesta no cambia), la
reserva se queda y el mes cuenta de más, nunca de menos.

El valor por defecto de `USD_PER_BUSY_SECOND` es el de la instancia `basic` (¼
vCPU y 1 GiB) con la CPU siempre activa: 0,25 × 0,00002 + 1 × 0,0000025. Es una
cota superior, porque la CPU solo se factura mientras trabaja. Con otro tipo de
instancia hay que cambiar este valor. Los precios son los de
[Cloudflare Containers](https://developers.cloudflare.com/containers/pricing/).

Lo que la estimación no cuenta:

- La memoria de una instancia encendida sin trabajo (`sleepAfter`, 5 minutos
  tras la última petición). Con tres instancias encendidas todo el mes son unos
  20 USD (3 × 0,0000025 × 2 592 000 s). La factura de Containers puede llegar al
  presupuesto más esa cifra.
- Una instancia que el Worker no logra detener al llegar al tope (se registra
  con `where: "stop"`). Cloudflare la factura hasta que se apague sola.
- Una instancia que sigue arrancando cuando se llega al tope no ha respondido
  aún, así que el Worker la detiene aunque otro alumno haya llegado a ella
  durante el arranque.

La suma de `cost_nano_usd` en el registro da el gasto estimado del mes.

### Turnstile

Cloudflare Turnstile se verifica en la primera ejecución de una sesión. Una
petición sin sesión y sin token recibe 403 `turnstile_missing` con la clave del
sitio en el campo `sitekey`. Con ella, `site/exercise.js` carga el widget, y
repite la petición con el token del widget en la cabecera `X-Turnstile-Token`.
El Worker lo comprueba con `siteverify`, al que envía solo el secreto y el
token, y si vale responde con la cookie `qg_session` además del resultado:

```text
qg_session=<caducidad>.<mac>; Max-Age=28800; Path=/run; HttpOnly; Secure; SameSite=Strict
```

La cookie lleva la hora de caducidad y un MAC que cubre esa hora y la IP. No
lleva ningún identificador, y no sirve desde otra IP ni pasada su caducidad. Las
siguientes ejecuciones la mandan solas y no vuelven a llamar a Turnstile.

| Respuesta | `reason`                | El alumno ve                                                                                           |
| --------- | ----------------------- | ------------------------------------------------------------------------------------------------------ |
| 403       | `turnstile_missing`     | «Antes de ejecutar código hay que comprobar que eres una persona.»                                     |
| 403       | `turnstile_failed`      | «No pasó la comprobación de que eres una persona. Recarga la página e inténtalo de nuevo.»             |
| 503       | `turnstile_unavailable` | «No se pudo comprobar que eres una persona. Vuelve a intentarlo en unos segundos.» (`Retry-After: 10`) |

| Variable             | Valor | Significa                               |
| -------------------- | ----- | --------------------------------------- |
| `SESSION_HOURS`      | 8     | Duración de la sesión verificada.       |
| `TURNSTILE_SITE_KEY` | —     | La clave pública del widget. Sin valor. |

`TURNSTILE_SECRET` es un secreto del Worker (`bindings.secret()`), no un valor
del repositorio. La clave del sitio no es secreta: el Worker se la da a la
página en la respuesta `turnstile_missing`. Cloudflare documenta claves de
prueba que no necesitan cuenta:

| Clave                                 | Tipo    | Comportamiento                                                |
| ------------------------------------- | ------- | ------------------------------------------------------------- |
| `1x00000000000000000000AA`            | sitio   | Siempre pasa. El token que genera es `XXXX.DUMMY.TOKEN.XXXX`. |
| `1x0000000000000000000000000000000AA` | secreto | Siempre pasa.                                                 |
| `2x0000000000000000000000000000000AA` | secreto | Siempre falla.                                                |
| `3x0000000000000000000000000000000AA` | secreto | Responde que el token ya se usó.                              |

Las pruebas del Worker usan los tres secretos.

### Qué recibe el contenedor y qué se registra

El contenedor recibe el cuerpo de la petición y `Content-Type`. No recibe la
cookie, el token ni la IP.

El Worker escribe estos registros y ningún otro. Todos tienen campos fijos, que
`src/log.ts` define.

1. Una línea `run` por cada petición a `/run` que el Worker contesta, con
   cualquier resultado menos un error interno:

   ```json
   {
     "event": "run",
     "outcome": "ok",
     "status": 200,
     "mode": "check",
     "exercise": "p1-quickstart/ghz",
     "code_bytes": 212,
     "busy_ms": 930,
     "cost_nano_usd": 6975
   }
   ```

   `outcome` es `ok`, `rate_minute`, `rate_day`, `bad_request`, `too_large`,
   `budget`, `turnstile_missing`, `turnstile_failed`, `turnstile_unavailable` o
   `run_too_long`. `mode` y `exercise` se copian solo si tienen la forma de un
   valor del contrato.

2. Una línea de error, en lugar de la anterior, cuando la petición falla por un
   error del Worker o de la configuración y responde 500 `internal_error`:

   ```json
   {
     "event": "run",
     "outcome": "internal_error",
     "status": 500,
     "error": "Error"
   }
   ```

   `error` es el nombre de la clase del error. `detail` lleva el texto solo si
   es un error de configuración, que nombra una variable y no datos.

3. Una línea de error aparte, además de la línea de la propia petición, cuando
   un paso posterior falla y la petición sigue su camino. Lleva `where` y no
   lleva `status`:
   - `"settle"`: falló el ajuste del presupuesto.
   - `"stop"`: falló detener una instancia al llegar al tope de la reserva.

Ningún registro lleva el código, la IP, el token, la cookie ni el texto de un
error. `cloudflare.config.ts` activa Workers Logs con el registro de
invocaciones apagado, que es el que lleva la petición. Lo que Cloudflare guarda
de su red no depende del Worker.

### Por qué estos valores

Los valores salen de las tarifas de Containers con la instancia `basic` y de
tres instancias que atienden un trabajo cada una:

- Un segundo de instancia ocupada cuesta como mucho 0,0000075 USD. Una ejecución
  que agota los 10 s de [Límites](#límites) cuesta 0,000075 USD.
- 30 por minuto es una ejecución cada 2 s. Con ejecuciones de 1 s una IP ocupa
  30 s de los 180 s de instancia que hay cada minuto.
- 1000 por día, todas de 10 s, cuestan 0,075 USD a una IP; de 1 s, 0,0075 USD.
- 20 USD son 2,7 millones de segundos de instancia ocupada, o 1,3 millones de
  ejecuciones de 2 s. Un atacante con muchas IPs llega antes al presupuesto que
  a una factura sin tope.

Son cálculos con esas tarifas, no medidas del Worker desplegado.
