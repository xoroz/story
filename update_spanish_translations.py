#!/usr/bin/env python3
"""
Script to update Spanish translations for StoryMagic
"""

import os
import re

# Path to the Spanish translation file
es_po_file = 'translations/es/LC_MESSAGES/messages.po'

# Spanish translations for the website
translations = {
    # Base template and Auth
    "StoryMagic": "StoryMagic",
    "Username/Email:": "Usuario/Email:",
    "Password:": "Contraseña:",
    "Invalid username/email or password.": "Usuario/email o contraseña inválidos.",
    "Home": "Inicio",
    "Create Story": "Crear Historia",
    "View Stories": "Ver Historias",
    "About": "Acerca de",
    "Login": "Iniciar Sesión",
    "Register": "Registrarse",
    "Credits": "Créditos",
    "Profile": "Perfil",
    "Logout": "Cerrar Sesión",
    "StoryMagic - AI-Powered Stories for Little Imaginations": "StoryMagic - Historias Impulsadas por IA para Pequeñas Imaginaciones",
    
    # About page
    "About StoryMagic": "Acerca de StoryMagic",
    "Version Information": "Información de Versión",
    "Current Version": "Versión Actual",
    "Project Overview": "Descripción del Proyecto",
    "StoryMagic is an AI-powered children's story generator that creates personalized stories based on your preferences.": "StoryMagic es un generador de cuentos infantiles impulsado por IA que crea historias personalizadas basadas en tus preferencias.",
    "Our mission is to inspire creativity and a love of reading in children through personalized storytelling experiences that are educational, engaging, and tailored to each child's interests.": "Nuestra misión es inspirar la creatividad y el amor por la lectura en los niños a través de experiencias de narración personalizadas que son educativas, atractivas y adaptadas a los intereses de cada niño.",
    "Key Features": "Características Principales",
    "Personalized stories based on age range, theme, and educational lessons": "Historias personalizadas basadas en rango de edad, tema y lecciones educativas",
    "Multiple language support (English, Spanish, Italian, Portuguese)": "Soporte para múltiples idiomas (Inglés, Español, Italiano, Portugués)",
    "Audio narration for an immersive experience": "Narración de audio para una experiencia inmersiva",
    "Various AI models to generate diverse storytelling styles": "Varios modelos de IA para generar diversos estilos de narración",
    "User accounts to save and manage your stories": "Cuentas de usuario para guardar y administrar tus historias",
    "How to Use StoryMagic": "Cómo Usar StoryMagic",
    "Create an account or log in": "Crea una cuenta o inicia sesión",
    "Click \"Create Story\" in the navigation menu": "Haz clic en \"Crear Historia\" en el menú de navegación",
    "Fill out the story preferences form": "Completa el formulario de preferencias de la historia",
    "Wait while our AI generates your personalized story": "Espera mientras nuestra IA genera tu historia personalizada",
    "Enjoy your story with optional audio narration": "Disfruta tu historia con narración de audio opcional",
    "Rate the story and create more!": "¡Califica la historia y crea más!",
    "Recent Changes": "Cambios Recientes",
    "No recent changes to display.": "No hay cambios recientes para mostrar.",
    "Contact Us": "Contáctanos",
    "Your Name": "Tu Nombre",
    "Your Email": "Tu Email",
    "Message": "Mensaje",
    "Human Verification": "Verificación Humana",
    "Please solve this simple math problem to verify you are human.": "Por favor, resuelve este simple problema matemático para verificar que eres humano.",
    "Send Message": "Enviar Mensaje",
    "Thank you for your message! We will get back to you soon.": "¡Gracias por tu mensaje! Nos pondremos en contacto contigo pronto.",
    "There was an error sending your message. Please try again later.": "Hubo un error al enviar tu mensaje. Por favor, inténtalo de nuevo más tarde.",
    "Please enter your name": "Por favor, ingresa tu nombre",
    "Please enter a valid email address": "Por favor, ingresa una dirección de email válida",
    "Please enter a message": "Por favor, ingresa un mensaje",
    "Please answer the verification question": "Por favor, responde la pregunta de verificación",
    "Incorrect answer to verification question": "Respuesta incorrecta a la pregunta de verificación",
    "Please enter a valid number for verification": "Por favor, ingresa un número válido para la verificación",
    
    # Index page
    "StoryMagic - AI-Powered Children's Stories": "StoryMagic - Historias Infantiles Impulsadas por IA",
    "AI-Powered Stories for Little Imaginations": "Historias Impulsadas por IA para Pequeñas Imaginaciones",
    "Creative Stories": "Historias Creativas",
    "Generate unique, imaginative stories tailored to your child's interests and age group.": "Genera historias únicas e imaginativas adaptadas a los intereses y edad de tu hijo.",
    "Educational": "Educativo",
    "Stories can include educational themes and valuable life lessons in an engaging format.": "Las historias pueden incluir temas educativos y valiosas lecciones de vida en un formato atractivo.",
    "Age-Appropriate": "Apropiado para la Edad",
    "Content is crafted specifically for your child's age range with appropriate vocabulary and themes.": "El contenido está creado específicamente para el rango de edad de tu hijo con vocabulario y temas apropiados.",
    "Create a Story": "Crear una Historia",
    
    # Create Story page
    "Create a Story - StoryMagic": "Crear una Historia - StoryMagic",
    "Recreate": "Recrear",
    "Create": "Crear",
    "a Magical Story": "una Historia Mágica",
    "Fill with Random Story": "Rellenar con Historia Aleatoria",
    "Story Details": "Detalles de la Historia",
    "Story Title": "Título de la Historia",
    "Enter a title for your story": "Ingresa un título para tu historia",
    "Age Range": "Rango de Edad",
    "Young Children (3-6 years)": "Niños Pequeños (3-6 años)",
    "Children (7-9 years)": "Niños (7-9 años)",
    "Older Children (10-12 years)": "Niños Mayores (10-12 años)",
    "Theme": "Tema",
    "What is the story about?": "¿De qué trata la historia?",
    "Describe what should happen in the story": "Describe lo que debería suceder en la historia",
    "Add specific details about the adventures, challenges, or special elements.": "Agrega detalles específicos sobre las aventuras, desafíos o elementos especiales.",
    "Lesson": "Lección",
    "Main Characters": "Personajes Principales",
    "Describe characters (e.g., 'a brave girl, a wise owl')": "Describe personajes (ej., 'una niña valiente, un búho sabio')",
    "Story Length": "Longitud de la Historia",
    "Short (5 min read)": "Corta (5 min de lectura)",
    "Medium (10 min read)": "Media (10 min de lectura)",
    "Long (15 min read)": "Larga (15 min de lectura)",
    "Language": "Idioma",
    "English": "Inglés",
    "Spanish": "Español",
    "Italian": "Italiano",
    "Portuguese": "Portugués",
    "Generate audio narration": "Generar narración de audio",
    "Private story (only visible to you)": "Historia privada (solo visible para ti)",
    "Choose AI Provider": "Elegir Proveedor de IA",
    "%(provider)s Model": "Modelo de %(provider)s",
}

def update_translation_file(file_path, translations):
    """Update the translation file with the provided translations."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # For each translation, find the msgid and update the msgstr
    for original, translation in translations.items():
        # Escape double quotes in the original and translation
        original_escaped = original.replace('"', '\\"')
        translation_escaped = translation.replace('"', '\\"')
        
        # Create the pattern to find the msgid and its corresponding msgstr
        pattern = f'msgid "{original_escaped}"\nmsgstr ""'
        replacement = f'msgid "{original_escaped}"\nmsgstr "{translation_escaped}"'
        
        # Replace in the content
        content = content.replace(pattern, replacement)
    
    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

if __name__ == "__main__":
    if update_translation_file(es_po_file, translations):
        print(f"Successfully updated Spanish translations in {es_po_file}")
    else:
        print(f"Failed to update translations in {es_po_file}")
