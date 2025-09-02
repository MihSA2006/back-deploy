from django.db import models, transaction
from django.db.models import F, Q
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.utils import timezone
from django.core.files.base import ContentFile
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from electeurs.models import Electeur
from elections.models import Election, Candidat
from electeur_auth.models import ElecteurAuth


class Vote(models.Model):
    id_vote = models.AutoField(primary_key=True)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="votes")
    electeur = models.ForeignKey(Electeur, on_delete=models.PROTECT, related_name="votes")
    candidat = models.ForeignKey(Candidat, on_delete=models.PROTECT, related_name="votes")

    tour = models.PositiveIntegerField(editable=False)
    date_vote = models.DateTimeField(auto_now_add=True)
    encrypted_candidat = models.TextField(editable=False)

    class Meta:
        unique_together = ('election', 'electeur', 'tour')  # un seul vote par électeur/tour

    def clean(self):
        # Vérifier que l'élection est en cours
        if self.election.status != "En cours":
            raise ValidationError("Impossible de voter pour une élection qui n’est pas en cours.")

        # Vérifier que le candidat appartient à l'élection
        if self.candidat.election_id != self.election.id_election:
            raise ValidationError("Le candidat n’appartient pas à cette élection.")

        # Vérifier que le tour correspond
        if self.tour != self.election.tourActuel:
            raise ValidationError("Le vote doit être au tour actuel de l’élection.")

        # Vérifier que l’électeur est bien authentifié
        now = timezone.now()
        session = ElecteurAuth.objects.filter(
            electeur=self.electeur,
            is_valid=True,
            expired_at__gt=now
        ).first()
        if not session:
            raise ValidationError("Électeur non authentifié ou session expirée.")

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Un vote ne peut pas être modifié.")

        # Associer le tour actuel
        self.tour = self.election.tourActuel

        # Crypter (ici simple masquage mais tu peux remplacer par du vrai chiffrement)
        self.encrypted_candidat = f"enc:{self.candidat.id_candidat}"

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Suppression de vote interdite (immutabilité).")


class Resultat(models.Model):
    id_resultat = models.AutoField(primary_key=True)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="resultats")
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name="resultats")
    tour = models.PositiveIntegerField()
    nb_votes = models.PositiveIntegerField(default=0)
    total_votes_election = models.PositiveIntegerField(default=0)
    taux_participation = models.DecimalField(max_digits=6, decimal_places=3, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ResultatFinale(models.Model):
    id_resultatFinale = models.AutoField(primary_key=True)
    election = models.OneToOneField(Election, on_delete=models.CASCADE, related_name="resultat_final")
    candidat_elu = models.ForeignKey(Candidat, on_delete=models.SET_NULL, null=True, blank=True, related_name="victoires")
    nb_vote_total_obtenu = models.PositiveIntegerField(default=0)
    taux_participation = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    tour_finale = models.PositiveIntegerField(default=1)
    date_finalisation = models.DateTimeField(default=timezone.now)

    archive_pdf = models.FileField(upload_to="archives_resultats/", null=True, blank=True)

    # ✅ Nouveau champ
    is_publish = models.BooleanField(default=False)

    def __str__(self):
        return f"Résultat final de {self.election}"



from django.db.models.signals import post_save
from django.dispatch import receiver


# Quand un vote est créé → mettre à jour les résultats
@receiver(post_save, sender=Vote)
def update_results_on_vote_created(sender, instance: Vote, created, **kwargs):
    if created:
        _recompute_and_update_resultats(instance.election, instance.tour, instance.candidat)


# Quand une élection se termine → figer résultats + PDF
@receiver(post_save, sender=Election)
def finalize_results_on_election_end(sender, instance: Election, **kwargs):
    if instance.status != "Terminée":
        return
    if hasattr(instance, "resultat_final"):
        return

    tour_final = instance.tourActuel
    resultats = Resultat.objects.filter(election=instance, tour=tour_final).order_by("-nb_votes")
    if not resultats.exists():
        return

    gagnant_res = resultats.first()
    final = ResultatFinale.objects.create(
        election=instance,
        candidat_elu=gagnant_res.candidat,
        nb_vote_total_obtenu=gagnant_res.nb_votes,
        taux_participation=gagnant_res.taux_participation,
        tour_finale=tour_final,
        date_finalisation=timezone.now(),
    )

    # Génération PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"Résultats finaux de l'élection: {str(instance)}", styles["Title"]))
    story.append(Paragraph(f"Date de finalisation : {timezone.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    data = [["Candidat", "Nombre de voix"]]
    for r in resultats:
        data.append([str(r.candidat), r.nb_votes])
    story.append(Table(data, hAlign="LEFT",
                       style=TableStyle([
                         ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                         ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                         ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                         ("GRID", (0, 0), (-1, -1), 1, colors.black),
                       ])))
    story.append(Spacer(1, 24))
    story.append(Paragraph(f"Gagnant : {gagnant_res.candidat} avec {gagnant_res.nb_votes} voix", styles["Heading2"]))
    story.append(Paragraph(f"Taux de participation : {float(gagnant_res.taux_participation):.2f}%", styles["Normal"]))
    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    final.archive_pdf.save(f"resultat_final_{instance.pk}.pdf", ContentFile(pdf_bytes))

    # Purge des votes de l’élection
    Vote.objects.filter(election=instance).delete()


# --- Fonctions utilitaires ---
def _compute_nb_inscrits_for_election(election: Election) -> int:
    return Electeur.objects.count()


def _recompute_and_update_resultats(election: Election, tour: int, voted_candidat: Candidat):
    with transaction.atomic():
        candidats_qs = Candidat.objects.select_for_update().filter(election=election)
        for cand in candidats_qs:
            Resultat.objects.get_or_create(
                election=election, candidat=cand, tour=tour,
                defaults={"nb_votes": 0, "total_votes_election": 0, "taux_participation": 0}
            )

        res = Resultat.objects.select_for_update().get(
            election=election, candidat=voted_candidat, tour=tour
        )
        res.nb_votes = F("nb_votes") + 1
        res.save(update_fields=["nb_votes"])

        total_votes = Vote.objects.filter(election=election, tour=tour).count()
        nb_inscrits = _compute_nb_inscrits_for_election(election)
        taux = (total_votes / nb_inscrits * 100) if nb_inscrits > 0 else 0

        Resultat.objects.filter(election=election, tour=tour).update(
            total_votes_election=total_votes,
            taux_participation=taux
        )
