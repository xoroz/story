#!/usr/bin/env python3
"""
Script to update Italian translations for StoryMagic
"""

import os
import re

# Path to the Italian translation file
it_po_file = 'translations/it/LC_MESSAGES/messages.po'

# Italian translations for the website
translations = {
    # Base template and Auth
    "StoryMagic": "StoryMagic",
    "Username/Email:": "Nome utente/Email:",
    "Password:": "Password:",
    "Invalid username/email or password.": "Nome utente/email o password non validi.",
    "Home": "Home",
    "Create Story": "Crea Storia",
    "View Stories": "Visualizza Storie",
    "Login": "Accedi",
    "Register": "Registrati",
    "Credits": "Crediti",
    "Profile": "Profilo",
    "Logout": "Esci",
    "StoryMagic - AI-Powered Stories for Little Imaginations": "StoryMagic - Storie Alimentate dall'IA per Piccole Immaginazioni",
    
    # Index page
    "StoryMagic - AI-Powered Children's Stories": "StoryMagic - Storie per Bambini Alimentate dall'IA",
    "AI-Powered Stories for Little Imaginations": "Storie Alimentate dall'IA per Piccole Immaginazioni",
    "Creative Stories": "Storie Creative",
    "Generate unique, imaginative stories tailored to your child's interests and age group.": "Genera storie uniche e fantasiose adattate agli interessi e all'età del tuo bambino.",
    "Educational": "Educativo",
    "Stories can include educational themes and valuable life lessons in an engaging format.": "Le storie possono includere temi educativi e preziose lezioni di vita in un formato coinvolgente.",
    "Age-Appropriate": "Adatto all'Età",
    "Content is crafted specifically for your child's age range with appropriate vocabulary and themes.": "Il contenuto è creato specificamente per la fascia d'età del tuo bambino con vocabolario e temi appropriati.",
    "Create a Story": "Crea una Storia",
    
    # Create Story page
    "Create a Story - StoryMagic": "Crea una Storia - StoryMagic",
    "Recreate": "Ricrea",
    "Create": "Crea",
    "a Magical Story": "una Storia Magica",
    "Fill with Random Story": "Riempi con Storia Casuale",
    "Story Details": "Dettagli della Storia",
    "Story Title": "Titolo della Storia",
    "Enter a title for your story": "Inserisci un titolo per la tua storia",
    "Age Range": "Fascia d'Età",
    "Young Children (3-6 years)": "Bambini Piccoli (3-6 anni)",
    "Children (7-9 years)": "Bambini (7-9 anni)",
    "Older Children (10-12 years)": "Bambini Più Grandi (10-12 anni)",
    "Theme": "Tema",
    "What is the story about?": "Di cosa parla la storia?",
    "Describe what should happen in the story": "Descrivi cosa dovrebbe accadere nella storia",
    "Add specific details about the adventures, challenges, or special elements.": "Aggiungi dettagli specifici sulle avventure, sfide o elementi speciali.",
    "Lesson": "Lezione",
    "Main Characters": "Personaggi Principali",
    "Describe characters (e.g., 'a brave girl, a wise owl')": "Descrivi i personaggi (es., 'una ragazza coraggiosa, un gufo saggio')",
    "Story Length": "Lunghezza della Storia",
    "Short (5 min read)": "Breve (5 min di lettura)",
    "Medium (10 min read)": "Media (10 min di lettura)",
    "Long (15 min read)": "Lunga (15 min di lettura)",
    "Language": "Lingua",
    "English": "Inglese",
    "Spanish": "Spagnolo",
    "Italian": "Italiano",
    "Portuguese": "Portoghese",
    "Generate audio narration": "Genera narrazione audio",
    "Private story (only visible to you)": "Storia privata (visibile solo a te)",
    "Choose AI Provider": "Scegli Fornitore di IA",
    "%(provider)s Model": "Modello %(provider)s",
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
    if update_translation_file(it_po_file, translations):
        print(f"Successfully updated Italian translations in {it_po_file}")
    else:
        print(f"Failed to update translations in {it_po_file}")
