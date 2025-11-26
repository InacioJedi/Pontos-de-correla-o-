import cv2
import numpy as np

def comparar_imagens():
    img1 = cv2.imread("imagem1.png")
    img2 = cv2.imread("imagem2.png")

    if img1 is None or img2 is None:
        print("Erro ao abrir imagens.")
        return

    # Redimensionar proporcionalmente
    altura = 900
    img1 = cv2.resize(img1, (int(img1.shape[1]*(altura/img1.shape[0])), altura))
    img2 = cv2.resize(img2, (int(img2.shape[1]*(altura/img2.shape[0])), altura))

    # DETECÇÃO MISTA — MAIS PONTOS E MAIS PRECISOS
    sift = cv2.SIFT_create(5000)
    akaze = cv2.AKAZE_create()

    kp1_sift, des1_sift = sift.detectAndCompute(img1, None)
    kp2_sift, des2_sift = sift.detectAndCompute(img2, None)

    kp1_ak, des1_ak = akaze.detectAndCompute(img1, None)
    kp2_ak, des2_ak = akaze.detectAndCompute(img2, None)

    # Combina keypoints e descritores
    # Combina APENAS keypoints - descritores continuam do SIFT
    kp1 = kp1_sift + kp1_ak
    kp2 = kp2_sift + kp2_ak
    des1 = des1_sift
    des2 = des2_sift   

    # FLANN matcher
    index_params = dict(algorithm=1, trees=5)
    flann = cv2.FlannBasedMatcher(index_params, {})

    matches = flann.knnMatch(des1, des2, k=2)

    # Teste de Lowe equilibrado
    bons = [m for m, n in matches if m.distance < 0.78 * n.distance]
    print(f"Total de bons matches (ratio test): {len(bons)}")

    if len(bons) < 10:
        print("Poucos pontos para análise!")
        return

    # Homografia + RANSAC para eliminar restos falsos
    src = np.float32([kp1[m.queryIdx].pt for m in bons]).reshape(-1,1,2)
    dst = np.float32([kp2[m.trainIdx].pt for m in bons]).reshape(-1,1,2)

    M, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    mask = mask.ravel().tolist()

    inliers = [bons[i] for i in range(len(bons)) if mask[i] == 1]
    print(f"Matches confiáveis após RANSAC: {len(inliers)}")

    # Limitar visual para ficar maneiro e não poluído
    inliers = inliers[:60]

    # Desenhar
    resultado = cv2.drawMatches(
        img1, kp1, img2, kp2, inliers, None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
    )

    cv2.imwrite("resultado_match.png", resultado)
    print("Imagem gerada: resultado_match.png")

    # Decisão final
    if len(inliers) > 18:
        print("🟢 As imagens são do mesmo local (alta confiança!)")
    else:
        print("🟡 Provavelmente do mesmo local, mas com baixa confiança")


if __name__ == "__main__":
    comparar_imagens()
