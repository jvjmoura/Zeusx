import pytesseract
from PIL import Image
import pdf2image
import io
import tempfile
import os
from typing import Union, List


pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


# Verificar se o Tesseract está acessível
try:
    print("Versão do Tesseract instalada:", pytesseract.get_tesseract_version())
except Exception as e:
    print("Erro ao acessar o Tesseract:", e)
class OCRProcessor:
    def __init__(self):
        import os
        # Tenta encontrar o Tesseract automaticamente
        tesseract_paths = [
            '/opt/homebrew/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/usr/bin/tesseract'
        ]
        
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"Encontrou Tesseract em: {path}")
                break
        
        print("Verificando versão do Tesseract...")
        try:
            version = pytesseract.get_tesseract_version()
            print(f"Tesseract versão: {version}")
        except Exception as e:
            print(f"Erro ao verificar Tesseract: {e}")

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Pré-processa a imagem para melhorar resultados do OCR."""
        try:
            # Converte para escala de cinza
            image = image.convert('L')
            
            # Aumenta o contraste
            from PIL import ImageEnhance, ImageFilter
            
            # Aplica desfoque gaussiano para reduzir ruído
            image = image.filter(ImageFilter.GaussianBlur(radius=1))
            
            # Aumenta o contraste
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Aumenta a nitidez
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Aumenta o brilho
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.5)
            
            return image
        except Exception as e:
            print(f"Erro no pré-processamento: {e}")
            return image  # Retorna imagem original em caso de erro

    def process_image(self, image: Union[str, bytes, Image.Image]) -> str:
        """Processa uma única imagem e retorna o texto."""
        if isinstance(image, str):
            # Se for caminho do arquivo
            image = Image.open(image)
        elif isinstance(image, bytes):
            # Se for bytes (upload de arquivo)
            image = Image.open(io.BytesIO(image))
        
        # Pré-processa a imagem
        image = self.preprocess_image(image)
        
        # Executa OCR
        text = pytesseract.image_to_string(image, lang='por')
        return text.strip()

    def process_pdf(self, pdf_path: str) -> str:
        """Processa um arquivo PDF e retorna o texto completo."""
        print(f"Processando PDF: {pdf_path}")
        try:
            # Converte PDF para imagens usando caminho explícito do poppler
            print("Convertendo PDF para imagens...")
            images = pdf2image.convert_from_path(
                pdf_path,
                poppler_path='/opt/homebrew/bin/',  # Caminho do poppler no Mac
                dpi=300  # Aumenta a resolução para melhor OCR
            )
            print(f"Converteu PDF em {len(images)} imagens")
            
            # Processa cada página
            texts = []
            for i, image in enumerate(images):
                print(f"Processando página {i+1}/{len(images)}")
                # Pré-processa a imagem
                image = self.preprocess_image(image)
                # Executa OCR com configurações otimizadas
                text = pytesseract.image_to_string(
                    image, 
                    lang='por',
                    config='--psm 1 --oem 3'  # Modo de segmentação automática e melhor engine
                )
                if text.strip():  # Se encontrou algum texto
                    texts.append(text)
                    print(f"Página {i+1}: Extraiu {len(text)} caracteres")
                else:
                    print(f"Página {i+1}: Nenhum texto encontrado")
            
            # Combina todos os textos
            final_text = "\n\n".join(texts)
            print(f"Total de caracteres extraídos: {len(final_text)}")
            return final_text
            
        except Exception as e:
            print(f"Erro ao processar PDF: {e}")
            import traceback
            print(traceback.format_exc())
            return ""

    def process_file(self, file) -> str:
        """Processa um arquivo (PDF ou imagem) e retorna o texto."""
        print(f"Iniciando OCR para arquivo: {file}")
        
        # Se for um objeto de arquivo do Streamlit
        if hasattr(file, 'read'):
            print("Processando arquivo do Streamlit")
            # Salva em arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp.write(file.read())
                temp_path = temp.name
                print(f"Arquivo temporário criado: {temp_path}")

            try:
                # Verifica a extensão
                extension = os.path.splitext(file.name)[1].lower()
                print(f"Extensão do arquivo: {extension}")
                if extension == '.pdf':
                    print("Convertendo PDF para imagens...")
                    text = self.process_pdf(temp_path)
                else:
                    # Assume que é uma imagem
                    text = self.process_image(temp_path)
                print(f"Texto extraído: {len(text)} caracteres")
                return text
            except Exception as e:
                print(f"Erro no OCR: {e}")
                import traceback
                print(traceback.format_exc())
                return ""
            finally:
                # Limpa o arquivo temporário
                os.unlink(temp_path)
                print("Arquivo temporário removido")
        
        # Se for um caminho de arquivo
        elif isinstance(file, str):
            if file.lower().endswith('.pdf'):
                return self.process_pdf(file)
            else:
                return self.process_image(file)
        
        raise ValueError("Tipo de arquivo não suportado")
