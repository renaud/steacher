Hello! For this exercise, write Python code to:

1. **Read a CSV file** named `temperatures.csv` that contains three columns: `Date`, `Sensor1`, and `Sensor2`.
2. **Extract the data** from the first and third columns.
3. **Store them** in a dictionary called `temps`, with the dates as keys and the temperatures from `Sensor2` as values.

Here is a preview of the content of the `temperatures.csv` file:

```csv
Date,Sensor1,Sensor2
02.10,10.7,32.3
04.10,12.5,31.8
09.10,15.2,33.0
...
```

Once your program executes successfully, it will store the data in the `temps` dictionary as follows:

```python
temps = {
    "02.10": 32.3,
    "04.10": 31.8,
    "09.10": 33.0,
    # etc ...
}
```

Would you like some hints, or would you prefer to try it yourself?