from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from datetime import date

class Region(models.Model):
    id_region = models.AutoField(primary_key=True)
    nom_region = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom_region

class District(models.Model):
    id_district = models.AutoField(primary_key=True)
    nom_district = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='districts')

    class Meta:
        unique_together = ('nom_district', 'region')

    def __str__(self):
        return self.nom_district

class Commune(models.Model):
    id_commune = models.AutoField(primary_key=True)
    nom_commune = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='communes')

    class Meta:
        unique_together = ('nom_commune', 'district')

    def __str__(self):
        return self.nom_commune

class Fokontany(models.Model):
    id_fokontany = models.AutoField(primary_key=True)
    nom_fokontany = models.CharField(max_length=100)
    nb_electeur_inscrit = models.PositiveIntegerField(default=0)
    commune = models.ForeignKey(Commune, on_delete=models.CASCADE, related_name='fokontanys')

    class Meta:
        unique_together = ('nom_fokontany', 'commune')

    def __str__(self):
        return self.nom_fokontany

    def increment_electeurs(self):
        self.nb_electeur_inscrit = models.F('nb_electeur_inscrit') + 1
        self.save(update_fields=['nb_electeur_inscrit'])

    def decrement_electeurs(self):
        self.nb_electeur_inscrit = models.F('nb_electeur_inscrit') - 1
        self.save(update_fields=['nb_electeur_inscrit'])



class Electeur(models.Model):
    id = models.AutoField(primary_key=True)
    nom_electeur = models.CharField(max_length=100)
    prenom_electeur = models.CharField(max_length=100)
    dateNaissance = models.DateField()
    lieuNaissance = models.CharField(max_length=100)
    numCIN = models.CharField(max_length=12, unique=True, validators=[
        RegexValidator(r'^\d{12}$', message='Le numéro CIN doit comporter exactement 12 chiffres.')
    ])
    adresse = models.CharField(max_length=255)
    profession = models.CharField(max_length=100)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    image = models.ImageField(upload_to='images/electeurs/', null=True, blank=True)
    numTel = models.CharField(max_length=20, unique=True, validators=[
        RegexValidator(r'^0\d{9}$', message='Le numéro de téléphone doit commencer par 0 et contenir 10 chiffres.')
    ])
    fokontany = models.ForeignKey("Fokontany", on_delete=models.CASCADE, related_name='electeurs')

    # 🆕 Champ pour savoir si l’électeur est apte à voter
    is_apte_vote = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nom_electeur} {self.prenom_electeur}"

    def age(self):
        today = date.today()
        return today.year - self.dateNaissance.year - (
            (today.month, today.day) < (self.dateNaissance.month, self.dateNaissance.day)
        )

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        # 🆕 Au moment de la création, définir automatiquement is_apte_vote selon l’âge
        if is_new:
            if self.age() >= 18:
                self.is_apte_vote = True
            else:
                self.is_apte_vote = False

        super().save(*args, **kwargs)

        if is_new:
            Fokontany.objects.filter(id_fokontany=self.fokontany.id_fokontany).update(
                nb_electeur_inscrit=models.F('nb_electeur_inscrit') + 1
            )

    def delete(self, *args, **kwargs):
        fokontany_id = self.fokontany.id_fokontany
        super().delete(*args, **kwargs)
        Fokontany.objects.filter(id_fokontany=fokontany_id).update(
            nb_electeur_inscrit=models.F('nb_electeur_inscrit') - 1
        )


# class Electeur(models.Model):
#     id = models.AutoField(primary_key=True)
#     nom_electeur = models.CharField(max_length=100)
#     prenom_electeur = models.CharField(max_length=100)
#     dateNaissance = models.DateField()
#     lieuNaissance = models.CharField(max_length=100)
#     numCIN = models.CharField(max_length=12, unique=True, validators=[
#         RegexValidator(r'^\d{12}$', message='Le numéro CIN doit comporter exactement 12 chiffres.')
#     ])
#     adresse = models.CharField(max_length=255)
#     profession = models.CharField(max_length=100)
#     email = models.EmailField(unique=True, validators=[EmailValidator()])
#     image = models.ImageField(upload_to='images/electeurs/', null=True, blank=True)
#     numTel = models.CharField(max_length=20, unique=True, validators=[
#         RegexValidator(r'^0\d{9}$', message='Le numéro de téléphone doit commencer par 0 et contenir 10 chiffres.')
#     ])
#     fokontany = models.ForeignKey(Fokontany, on_delete=models.CASCADE, related_name='electeurs')

#     def __str__(self):
#         return f"{self.nom_electeur} {self.prenom_electeur}"

#     def save(self, *args, **kwargs):
#         is_new = self._state.adding
#         super().save(*args, **kwargs)
#         if is_new:
#             Fokontany.objects.filter(id_fokontany=self.fokontany.id_fokontany).update(
#                 nb_electeur_inscrit=models.F('nb_electeur_inscrit') + 1
#             )

#     def delete(self, *args, **kwargs):
#         fokontany_id = self.fokontany.id_fokontany
#         super().delete(*args, **kwargs)
#         Fokontany.objects.filter(id_fokontany=fokontany_id).update(
#             nb_electeur_inscrit=models.F('nb_electeur_inscrit') - 1
#         )
