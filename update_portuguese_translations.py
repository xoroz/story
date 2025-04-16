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
    # Base template and Auth
    "StoryMagic": "StoryMagic",
    "Username/Email:": "Usuário/Email:",
    "Password:": "Senha:",
    "Invalid username/email or password.": "Usuário/email ou senha inválidos.",
    "Home": "Início",
    "Create Story": "Criar História",
    "View Stories": "Ver Histórias",
    "About": "Sobre",
    "Login": "Entrar",
    "Register": "Registrar",
    "Credits": "Créditos",
    "Profile": "Perfil",
    "Logout": "Sair",
    "StoryMagic - AI-Powered Stories for Little Imaginations": "StoryMagic - Histórias Impulsionadas por IA para Pequenas Imaginações",
    
    # About page
    "About StoryMagic": "Sobre StoryMagic",
    "Version Information": "Informações de Versão",
    "Current Version": "Versão Atual",
    "Project Overview": "Visão Geral do Projeto",
    "StoryMagic is an AI-powered children's story generator that creates personalized stories based on your preferences.": "StoryMagic é um gerador de histórias infantis baseado em IA que cria histórias personalizadas com base nas suas preferências.",
    "Our mission is to inspire creativity and a love of reading in children through personalized storytelling experiences that are educational, engaging, and tailored to each child's interests.": "Nossa missão é inspirar a criatividade e o amor pela leitura nas crianças através de experiências de narração personalizadas que são educativas, envolventes e adaptadas aos interesses de cada criança.",
    "Key Features": "Principais Características",
    "Personalized stories based on age range, theme, and educational lessons": "Histórias personalizadas baseadas em faixa etária, tema e lições educativas",
    "Multiple language support (English, Spanish, Italian, Portuguese)": "Suporte a múltiplos idiomas (Inglês, Espanhol, Italiano, Português)",
    "Audio narration for an immersive experience": "Narração de áudio para uma experiência imersiva",
    "Various AI models to generate diverse storytelling styles": "Vários modelos de IA para gerar diversos estilos de narração",
    "User accounts to save and manage your stories": "Contas de usuário para salvar e gerenciar suas histórias",
    "How to Use StoryMagic": "Como Usar o StoryMagic",
    "Create an account or log in": "Crie uma conta ou faça login",
    "Click \"Create Story\" in the navigation menu": "Clique em \"Criar História\" no menu de navegação",
    "Fill out the story preferences form": "Preencha o formulário de preferências da história",
    "Wait while our AI generates your personalized story": "Aguarde enquanto nossa IA gera sua história personalizada",
    "Enjoy your story with optional audio narration": "Aproveite sua história com narração de áudio opcional",
    "Rate the story and create more!": "Avalie a história e crie mais!",
    "Recent Changes": "Mudanças Recentes",
    "No recent changes to display.": "Nenhuma mudança recente para exibir.",
    "Contact Us": "Contate-nos",
    "Your Name": "Seu Nome",
    "Your Email": "Seu Email",
    "Message": "Mensagem",
    "Human Verification": "Verificação Humana",
    "Please solve this simple math problem to verify you are human.": "Por favor, resolva este simples problema matemático para verificar que você é humano.",
    "Send Message": "Enviar Mensagem",
    "Thank you for your message! We will get back to you soon.": "Obrigado pela sua mensagem! Entraremos em contato em breve.",
    "There was an error sending your message. Please try again later.": "Houve um erro ao enviar sua mensagem. Por favor, tente novamente mais tarde.",
    "Please enter your name": "Por favor, digite seu nome",
    "Please enter a valid email address": "Por favor, digite um endereço de email válido",
    "Please enter a message": "Por favor, digite uma mensagem",
    "Please answer the verification question": "Por favor, responda à pergunta de verificação",
    "Incorrect answer to verification question": "Resposta incorreta à pergunta de verificação",
    "Please enter a valid number for verification": "Por favor, digite um número válido para verificação",
    
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
