Bonjour! Pour cet exercice, écrivez du code Python pour :

1. **Lire un fichier CSV** nommé `temperatures.csv` qui contient trois colonnes : `Date`, `Sensor1` et `Sensor2`.
2. **Extraire les données** des première et troisième colonnes.
3. **Les stocker** dans un dictionnaire appelé `temps`, avec les dates comme clés et les températures de `Sensor2` comme valeurs.

Voici un aperçu du contenu du fichier `temperatures.csv` :

```csv
Date,Sensor1,Sensor2
02.10,10.7,32.3
04.10,12.5,31.8
09.10,15.2,33.0
...
```

Une fois votre programme exécuté avec succès, il stockera les données dans le dictionnaire `temps` comme suit :

```python
temps = {
    "02.10": 32.3,
    "04.10": 31.8,
    "09.10": 33.0,
    # etc ...
}
```

Souhaitez-vous quelques indices ou préférez-vous essayer vous-même ?