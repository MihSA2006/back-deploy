import cv2
import face_recognition
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def resize_image(image, width=500):
    h, w = image.shape[:2]
    ratio = width / w
    resized = cv2.resize(image, (width, int(h * ratio)), interpolation=cv2.INTER_AREA)
    return resized  # Retourne seulement l'image redimensionnée


def preprocess_image(image):
    # Normalisation de la luminosité
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def align_face(image, landmarks):
    if 'left_eye' not in landmarks or 'right_eye' not in landmarks:
        return image

    left_eye = np.mean(landmarks['left_eye'], axis=0)
    right_eye = np.mean(landmarks['right_eye'], axis=0)

    dY = right_eye[1] - left_eye[1]
    dX = right_eye[0] - left_eye[0]
    angle = np.degrees(np.arctan2(dY, dX))

    eyes_center = ((left_eye[0] + right_eye[0]) // 2,
                   ((left_eye[1] + right_eye[1]) // 2))

    M = cv2.getRotationMatrix2D(eyes_center, angle, 1.0)
    aligned = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]),
                             flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)
    return aligned


def draw_landmarks(image, landmarks_list):
    for landmarks in landmarks_list:
        for feature, points in landmarks.items():
            for i in range(1, len(points)):
                cv2.line(image, points[i-1], points[i], (255, 0, 0), 1)
            for point in points:
                cv2.circle(image, point, 2, (0, 255, 0), -1)

def compare_faces(img1_path, img2_path, threshold=0.2):
    print(f"\n🔄 Fonction compare_faces lancée")
    print(f"   - Image 1 : {img1_path}")
    print(f"   - Image 2 : {img2_path}")

    # Chargement
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    if img1 is None or img2 is None:
        print("❌ Erreur de chargement d'une ou des images")
        return False, 0.0

    print("✅ Images chargées correctement")

    # Pré-traitement
    img1 = preprocess_image(img1)
    img2 = preprocess_image(img2)
    print("🔧 Images prétraitées")

    img1 = resize_image(img1)
    img2 = resize_image(img2)
    print("📏 Images redimensionnées")

    rgb1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
    rgb2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

    loc1 = face_recognition.face_locations(rgb1)
    loc2 = face_recognition.face_locations(rgb2)

    print(f"📌 Visages détectés : {len(loc1)} dans image1, {len(loc2)} dans image2")

    if not loc1 or not loc2:
        print("❌ Aucun visage détecté dans l'une des images")
        return False, 0.0

    landmarks1 = face_recognition.face_landmarks(rgb1, loc1)
    landmarks2 = face_recognition.face_landmarks(rgb2, loc2)
    print("🗺️ Landmarks détectés")

    aligned1 = align_face(rgb1, landmarks1[0])
    aligned2 = align_face(rgb2, landmarks2[0])
    print("📐 Visages alignés")

    encoding1 = face_recognition.face_encodings(aligned1, known_face_locations=[loc1[0]])[0]
    encoding2 = face_recognition.face_encodings(aligned2, known_face_locations=[loc2[0]])[0]
    print("🧬 Encodage des visages terminé")

    distance = face_recognition.face_distance([encoding1], encoding2)[0]
    cosine_sim = cosine_similarity([encoding1], [encoding2])[0][0]
    match = distance < threshold

    print("\n🔍 Résultats détaillés :")
    print(f"   - Seuil de tolérance: {threshold}")
    print(f"   - Correspondance: {'✅ OUI' if match else '❌ NON'}")
    print(f"   - Distance euclidienne: {distance:.4f}")
    print(f"   - Similarité cosinus: {cosine_sim * 100:.2f}%")

    draw_landmarks(img1, face_recognition.face_landmarks(rgb1))
    draw_landmarks(img2, face_recognition.face_landmarks(rgb2))

    # cv2.imshow('Image 1 (avec landmarks)', img1)
    # cv2.imshow('Image 2 (avec landmarks)', img2)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return match, distance
