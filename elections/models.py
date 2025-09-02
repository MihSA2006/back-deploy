from django.db import models
from django.utils import timezone
from electeurs.models import Electeur  # on suppose que l'app s'appelle electeurs

class TypeElection(models.Model):
    id_type_election = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.titre

class Election(models.Model):
    STATUS_CHOICES = [
        ('En préparation', 'En préparation'),
        ('En cours', 'En cours'),
        ('Terminée', 'Terminée'),
        ('Annulée', 'Annulée'),
    ]

    id_election = models.AutoField(primary_key=True)
    type_election = models.ForeignKey(TypeElection, on_delete=models.CASCADE, related_name='elections')
    nb_candidat_inscrit = models.PositiveIntegerField(default=0)
    dateDebut = models.DateTimeField()
    dateFin = models.DateTimeField(editable=False)
    dateCreation = models.DateTimeField(auto_now_add=True)
    tourActuel = models.PositiveIntegerField(default=1, editable=False)
    seuilMajorite = models.PositiveIntegerField(default=50, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='En préparation')

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new:
            self.dateFin = self.dateDebut + timezone.timedelta(days=1)
            self.status = 'En préparation'

        if self.status != "Annulée":
            self.update_status()

        super().save(*args, **kwargs)


    def update_status(self):
        if self.status == "Annulée":
            return

        now = timezone.now()
        if now < self.dateDebut:
            self.status = 'En préparation'
        elif self.dateDebut <= now < self.dateFin:
            self.status = 'En cours'
        else:
            self.status = 'Terminée'

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.dateDebut <= timezone.now():
            raise ValidationError("La date de début doit être dans le futur.")

        existing = Election.objects.filter(
            type_election=self.type_election,
            status__in=['En préparation', 'En cours']
        )
        if self.pk:
            existing = existing.exclude(pk=self.pk)

        if existing.exists():
            raise ValidationError("Une élection de ce type existe déjà en préparation ou en cours.")

    def __str__(self):
        return f"{self.type_election.titre} - {self.dateDebut.date()}"



class Candidat(models.Model):
    id_candidat = models.AutoField(primary_key=True)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidats')
    id_electeur = models.OneToOneField(Electeur, on_delete=models.CASCADE)
    numCandidat = models.PositiveIntegerField()
    pseudo = models.CharField(max_length=100, null=True, blank=True)
    dateInscription = models.DateTimeField(auto_now_add=True)
    biographie = models.TextField()
    photo_candidat = models.ImageField(upload_to='images/candidats/')
    estQualifieTour2 = models.BooleanField(default=False)

    class Meta:
        unique_together = ('election', 'numCandidat')

    def save(self, *args, **kwargs):
        if self.election.status == 'En cours':
            raise ValueError("Impossible d’ajouter ou modifier un candidat pour une élection en cours.")
        super().save(*args, **kwargs)
        Election.objects.filter(pk=self.election.pk).update(nb_candidat_inscrit=models.F('nb_candidat_inscrit') + 1)

    def delete(self, *args, **kwargs):
        if self.election.status == 'En cours':
            raise ValueError("Impossible de supprimer un candidat pendant une élection en cours.")
        Election.objects.filter(pk=self.election.pk).update(nb_candidat_inscrit=models.F('nb_candidat_inscrit') - 1)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Candidat #{self.numCandidat} ({self.id_electeur.nom_electeur})"
