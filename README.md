# Tasks

- Intentar explotar totes les features que poguem (mapa, dns, ...)
- Pensar la Infraestructura de xarxa
- Omplir why_is_it_useful (model de negoci)
- Automatitzar el config
- Probar-ho a la rasp

## Network architecture

Target architecture for router without flow recording capabilities:
```
    +-------+
    |  ISP  |
    +-------+
        |
        |
   +----------+
   |  Router  |
   +----------+
        |
        |
+----------------+
|  Raspberry PI  |
+----------------+
        |
        |
   +----------+
   |  Switch  |
   +----------+
```

Actual wiring:

```
    +-------+
    |  ISP  |
    +-------+
        |
        |                  Acts as HUB
   +----------+  VLAN0  +----------------+
   |  Router  |---------|  Raspberry PI  |
   +----------+  VLAN1  +----------------+
        |
        | VLAN1
        |
+-------------------------+
|  Other network devices  |
+-------------------------+
```

If the router supports flow recording, architecture is not as important as the Raspberry does not need to see all the traffic.
```
    +-------+
    |  ISP  |
    +-------+
        |
        |
   +----------+
   |  Router  |
   +----------+
        |
        |
   +----------+    +----------------+
   |  Switch  |----|  Raspberry PI  |
   +----------+    +----------------+
        |
        |
+-------------------------+
|  Other network devices  |
+-------------------------+
```

