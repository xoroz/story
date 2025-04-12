#!/usr/bin/env python3
"""
Script to update Portuguese translations for StoryMagic
"""

import os
import re

# Path to the Portuguese translation file
pt_po_file = 'translations/pt/LC_MESSAGES/messages.po'

# Portuguese translations for the website
translations = {
    # Base template
    "StoryMagic": "StoryMagic",
    "Home": "Início",
    "Create Story": "Criar História",
    "View Stories": "Ver Histórias",
    "Login": "Entrar",
    "Register": "Registrar",
    "Credits": "Créditos",
    "Profile": "Perfil",
    "Logout": "Sair",
    "StoryMagic - AI-Powered Stories for Little Imaginations": "StoryMagic - Histórias Impulsionadas por IA para Pequenas Imaginações",
    
    # Index page
    "StoryMagic - AI-Powered Children's Stories": "StoryMagic - Histórias Infantis Impulsionadas por IA",
    "AI-Powered Stories for Little Imaginations": "Histórias Impulsionadas por IA para Pequenas Imaginações",
    "Creative Stories": "Histórias Criativas",
    "Generate unique, imaginative stories tailored to your child's interests and age group.": "Gere histórias únicas e imaginativas adaptadas aos interesses e idade do seu filho.",
    "Educational": "Educativo",
    "Stories can include educational themes and valuable life lessons in an engaging format.": "As histórias podem incluir temas educativos e valiosas lições de vida em um formato envolvente.",
    "Age-Appropriate": "Adequado à Idade",
    "Content is crafted specifically for your child's age range with appropriate vocabulary and themes.": "O conteúdo é criado especificamente para a faixa etária do seu filho com vocabulário e temas apropriados.",
    "Create a Story": "Criar uma História",
    
    # Create Story page
    "Create a Story - StoryMagic": "Criar uma História - StoryMagic",
    "Recreate": "Recriar",
    "Create": "Criar",
    "a Magical Story": "uma História Mágica",
    "Fill with Random Story": "Preencher com História Aleatória",
    "Story Details": "Detalhes da História",
    "Story Title": "Título da História",
    "Enter a title for your story": "Digite um título para sua história",
    "Age Range": "Faixa Etária",
    "Young Children (3-6 years)": "Crianças Pequenas (3-6 anos)",
    "Children (7-9 years)": "Crianças (7-9 anos)",
    "Older Children (10-12 years)": "Crianças Mais Velhas (10-12 anos)",
    "Theme": "Tema",
    "What is the story about?": "Sobre o que é a história?",
    "Describe what should happen in the story": "Descreva o que deve acontecer na história",
    "Add specific details about the adventures, challenges, or special elements.": "Adicione detalhes específicos sobre as aventuras, desafios ou elementos especiais.",
    "Lesson": "Lição",
    "Main Characters": "Personagens Principais",
    "Describe characters (e.g., 'a brave girl, a wise owl')": "Descreva personagens (ex., 'uma menina corajosa, uma coruja sábia')",
    "Story Length": "Comprimento da História",
    "Short (5 min read)": "Curta (5 min de leitura)",
    "Medium (10 min read)": "Média (10 min de leitura)",
    "Long (15 min read)": "Longa (15 min de leitura)",
    "Language": "Idioma",
    "English": "Inglês",
    "Spanish": "Espanhol",
    "Italian": "Italiano",
    "Portuguese": "Português",
    "Generate audio narration": "Gerar narração de áudio",
    "Private story (only visible to you)": "História privada (visível apenas para você)",
    "Choose AI Provider": "Escolher Provedor de IA",
    "%(provider)s Model": "Modelo %(provider)s",
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
    if update_translation_file(pt_po_file, translations):
        print(f"Successfully updated Portuguese translations in {pt_po_file}")
    else:
        print(f"Failed to update translations in {pt_po_file}")
