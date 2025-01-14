Hallo! Für diese Übung schreiben Sie Python-Code, um:

1. **Eine CSV-Datei lesen** namens `temperatures.csv`, die drei Spalten enthält: `Date`, `Sensor1` und `Sensor2`.
2. **Die Daten extrahieren** aus der ersten und dritten Spalte.
3. **Diese speichern** in einem Wörterbuch namens `temps`, wobei die Daten als Schlüssel und die Temperaturen von `Sensor2` als Werte verwendet werden.

Hier ist ein Überblick über den Inhalt der Datei `temperatures.csv`:

```csv
Date,Sensor1,Sensor2
02.10,10.7,32.3
04.10,12.5,31.8
09.10,15.2,33.0
...
```

Sobald Ihr Programm erfolgreich ausgeführt wurde, werden die Daten im Wörterbuch `temps` wie folgt gespeichert:

```python
temps = {
    "02.10": 32.3,
    "04.10": 31.8,
    "09.10": 33.0,
    # usw ...
}
```

Möchten Sie einige Hinweise oder möchten Sie es selbst ausprobieren?