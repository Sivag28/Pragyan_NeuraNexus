"""
Hospital Assistant Chatbot
Designed for hospital staff and patients with multilingual support
"""

import re
from datetime import datetime


def detect_language(text):
    """Detect language from text"""
    if not text:
        return 'en'
    
    text = text.strip().lower()
    
    # Check for Tamil
    if re.search(r'[\u0b80-\u0bff]', text):
        return 'ta'
    # Check for Hindi
    if re.search(r'[\u0900-\u097f]', text):
        return 'hi'
    # Check for Chinese
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'zh-cn'
    # Check for Spanish
    if re.search(r'[ñáéíóúü¡¿]', text.lower()):
        return 'es'
    # Check for French
    if re.search(r'[àâçéèêëîïôûùüÿ]', text.lower()):
        return 'fr'
    # Check for German
    if re.search(r'[äöüß]', text.lower()):
        return 'de'
    
    return 'en'


class HospitalChatbot:
    def __init__(self):
        self.conversation_history = []
        self.current_language = 'en'
        
    def process_message(self, user_input):
        """Process user message and return response"""
        if not user_input or not user_input.strip():
            return self._get_help_response()
        
        user_input = user_input.strip()
        original_input = user_input  # Keep original for Tamil matching
        self.current_language = detect_language(user_input)
        
        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # For Tamil/Hindi/other non-latin scripts, use original text for matching
        # For English and other latin scripts, use lowercase
        if self.current_language in ['ta', 'hi', 'zh-cn']:
            response = self._generate_response(original_input)
        else:
            response = self._generate_response(user_input.lower())
        
        # Add response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def _generate_response(self, user_input):
        """Generate response based on user input"""
        lang = self.current_language
        
        # Greetings
        greetings = {
            'en': "Hello! I'm your Hospital Assistant. How can I help you today?",
            'ta': "வணக்கம்! நான் உங்கள் மருத்துவமனை உதவியாளர். இன்று உங்களுக்கு எப்படி உதவ முடியும்?",
            'hi': "नमस्ते! मैं आपका अस्पताल सहायक हूं। मैं आज आपकी कैसे मदद कर सकता हूं?",
            'es': "¡Hola! Soy tu Asistente Hospitalario. ¿Cómo puedo ayudarte hoy?",
            'fr': "Bonjour! Je suis votre Assistant Hospitalier. Comment puis-je vous aider?",
            'de': "Hallo! Ich bin Ihr Krankenhausassistent. Wie kann ich Ihnen helfen?",
            'zh-cn': "您好！我是您的医院助理。今天我能为您做些什么？"
        }
        
        if any(p in user_input for p in ['hello', 'hi', 'hey', 'namaste', 'hola', 'bonjour']):
            return greetings.get(lang, greetings['en'])
        
        # Thank you
        if any(p in user_input for p in ['thank', 'thanks', 'gracias', 'merci', 'shukriya']):
            thanks = {
                'en': "You're welcome! Is there anything else I can help you with?",
                'ta': "வரவேற்கிறேன்! வேறு ஏதாவது உதவி தேவைதானா?",
                'hi': "कोई बात नहीं! क्या मैं आपकी और मदद कर सकता हूं?",
                'es': "¡De nada! ¿Hay algo más en lo que pueda ayudarte?",
                'fr': "De rien! Y a-t-il autre chose que je puisse faire pour vous?",
                'de': "Gerne! Gibt es noch etwas, womit ich helfen kann?",
                'zh-cn': "不客气！还有什么我可以帮您的吗？"
            }
            return thanks.get(lang, thanks['en'])
        
        # Goodbye
        if any(p in user_input for p in ['bye', 'goodbye', 'adios', 'au revoir']):
            goodbye = {
                'en': "Goodbye! Feel free to reach out anytime you need assistance.",
                'ta': "விடைபெறுகிறேன்! உதவி தேவைப்படலாம்நீங்கள் தொடர்பு கொள்ளலாம!",
                'hi': "अलविदा! मदद की जरूरत हो तो संपर्क करें।",
                'es': "¡Adiós! No dude en contactarnos cuando necesite asistencia.",
                'fr': "Au revoir! N'hésitez pas à nous contacter si vous avez besoin d'aide.",
                'de': "Auf Wiedersehen! Kontaktieren Sie uns bei Bedarf jederzeit.",
                'zh-cn': "再见！如需帮助，请随时联系我们。"
            }
            return goodbye.get(lang, goodbye['en'])
        
        # Emergency questions
        if any(p in user_input for p in ['emergency', 'urgent', 'critical', 'severe', 'ambulance', 'heart attack', 'stroke']):
            return self._get_emergency_response(lang)
        
        # Department information - English
        if any(p in user_input.lower() for p in ['department', 'departments', 'which department', 'tell me about']):
            return self._get_department_info(lang)
        
        # Department information - Tamil
        if any(p in user_input for p in ['துறை', 'துறைகள்', 'துறை தகவல்', 'துறை தகவல் மற்று இடங்கள்', 'மருத்துவமனை துறைகள்', 'துறைகள் மற்று அவற்றின் சேவைகள்', 'துறைகள் மற்று சேவைகள்']):
            return self._get_department_info(lang)
        
        # Department information - Hindi
        if any(p in user_input for p in ['विभाग', 'विभागों', 'विभाग जानकारी', 'विभाग सूचना']):
            return self._get_department_info(lang)
        
        # Specific departments
        if 'emergency' in user_input:
            return self._get_department_detail('Emergency', lang)
        if any(p in user_input for p in ['cardio', 'heart', 'cardiology']):
            return self._get_department_detail('Cardiology', lang)
        if any(p in user_input for p in ['neuro', 'brain', 'nerve', 'headache']):
            return self._get_department_detail('Neurology', lang)
        if any(p in user_input for p in ['ortho', 'bone', 'joint', 'fracture']):
            return self._get_department_detail('Orthopedics', lang)
        if any(p in user_input for p in ['child', 'pediatric', 'kids']):
            return self._get_department_detail('Pediatrics', lang)
        if 'icu' in user_input:
            return self._get_department_detail('ICU', lang)
        
        # Wait times
        if any(p in user_input for p in ['wait', 'time', 'appointment', 'how long']):
            return self._get_wait_time(lang)
        
        # Admission
        if any(p in user_input for p in ['admission', 'admit', 'register', 'new patient']):
            return self._get_admission_info(lang)
        
        # Vital signs
        if any(p in user_input for p in ['vital', 'blood pressure', 'heart rate', 'temperature', 'oxygen']):
            return self._get_vitals_info(lang)
        
        # Medication
        if any(p in user_input for p in ['medication', 'medicine', 'drug', 'prescription', 'pharmacy']):
            return self._get_medication_info(lang)
        
        # Visiting hours
        if any(p in user_input for p in ['visitor', 'visiting', 'family', 'hours']):
            return self._get_visiting_hours(lang)
        
        # Lab results
        if any(p in user_input for p in ['lab', 'test', 'blood test', 'results', 'report']):
            return self._get_lab_info(lang)
        
        # Symptoms
        if any(p in user_input for p in ['symptom', 'pain', 'feeling', 'sick']):
            return self._get_symptoms_info(lang)
        
        # Help request
        if any(p in user_input for p in ['help', 'what can you do', 'assist']):
            return self._get_help_response(lang)
        
        # Language switching - switch to Tamil
        if any(p in user_input for p in ['speak tamil', 'tamil', 'in tamil', 'switch to tamil', 'தமிழ்']):
            self.current_language = 'ta'
            return self._get_help_response('ta')
        
        # Language switching - switch to Hindi
        if any(p in user_input for p in ['speak hindi', 'hindi', 'in hindi', 'switch to hindi', 'हिंदी']):
            self.current_language = 'hi'
            return self._get_help_response('hi')
        
        # Language switching - switch to Spanish
        if any(p in user_input for p in ['speak spanish', 'spanish', 'in spanish', 'español']):
            self.current_language = 'es'
            return self._get_help_response('es')
        
        # Language switching - switch to French
        if any(p in user_input for p in ['speak french', 'french', 'in french', 'français']):
            self.current_language = 'fr'
            return self._get_help_response('fr')
        
        # Language switching - switch to German
        if any(p in user_input for p in ['speak german', 'german', 'in german', 'deutsch']):
            self.current_language = 'de'
            return self._get_help_response('de')
        
        # Language switching - switch to Chinese
        if any(p in user_input for p in ['speak chinese', 'chinese', 'in chinese', '中文']):
            self.current_language = 'zh-cn'
            return self._get_help_response('zh-cn')
        
        # Default - try to give helpful response
        return self._get_default_response(lang, user_input)
    
    def _get_emergency_response(self, lang):
        """Get emergency response"""
        responses = {
            'en': "🚨 EMERGENCY: For life-threatening situations, call emergency services immediately!\n\nFor critical patients:\n1. Ensure patient safety\n2. Call emergency team\n3. Monitor vitals\n4. Prepare for immediate intervention\n\nIf this is an emergency, please call your local emergency number now!",
            'ta': "🚨 அவசரநடவடிக்கை: உயிர் угроза நிலைமைகளுக்கு, உடனடியாக அவசர சேவைகளை அழைக்கவும்!\n\nமுக்கிய நோயாளிகள்:\n1. நோயாளி பாதுகாப்பை உறுதிசெய்க\n2. அவசர குழுவை அழைக்க\n3. உயிர் அளவீடுகளைக் கண்காணி\n4. உடனடி தலையீடுக்கு தயாராகு",
            'hi': "🚨 आपातकालीन: जानलेवा स्थिति के लिए तुरंत आपातकालीन सेवाओं को कॉल करें!\n\nगंभीर रोगियों के लिए:\n1. रोगी की सुरक्षा सुनिश्चित करें\n2. आपातकालीन टीम को कॉल करें\n3. जीवन चिह्नों की निगरानी करें\n4. तुरंत हस्तक्षेप के लिए तैयार हों",
            'es': "🚨 EMERGENCIA: ¡Para situaciones potencialmente mortales, llame a los servicios de emergencia inmediatamente!\n\nPara pacientes críticos:\n1. Asegure la seguridad del paciente\n2. Llame al equipo de emergencia\n3. Monitoree los signos vitales\n4. Prepárese para intervención inmediata",
            'fr': "🚨 URGENCE: Pour les situations potentiellement mortelles, appelez les services d'urgence immédiatement!\n\nPour les patients critiques:\n1. Assurez la sécurité du patient\n2. Appelez l'équipe d'urgence\n3. Surveillez les signes vitaux\n4. Préparez-vous pour une intervention immédiate",
            'de': "🚨 NOTFALL: Bei lebensbedrohlichen Situationen rufen Sie sofort den Notdienst!\n\nFür kritische Patienten:\n1. Patientensicherheit gewährleisten\n2. Notfallteam rufen\n3. Vitalzeichen überwachen\n4. Auf sofortige Intervention vorbereiten",
            'zh-cn': "🚨 紧急情况：对于危及生命的情况，请立即拨打急救电话！\n\n对于危重病人：\n1. 确保病人安全\n2. 呼叫急救团队\n3. 监测生命体征\n4. 准备立即干预"
        }
        return responses.get(lang, responses['en'])
    
    def _get_department_info(self, lang):
        """Get department information"""
        responses = {
            'en': "🏥 Our Hospital Departments:\n\n• Emergency - Critical & life-threatening conditions\n• Cardiology - Heart & cardiovascular issues\n• Neurology - Brain & nervous system\n• Orthopedics - Bones, joints & muscles\n• Pediatrics - Children's health\n• General Medicine - Common ailments\n• ICU - Critical care\n\nWhich department would you like to know more about?",
            'ta': "🏥 எங்கள் மருத்துவமனை துறைகள்:\n\n• அவசரநடவடிக்கை - முக்கிய & உயிர் угроза நிலைமைகள்\n• இதயவியல் - இதய & இரத்த நாள பிரச்சினைகள்\n• நரம்பியல் - மூளை & நரம்பு அமைப்பு\n• ஆர்தோபெடிக்ஸ் - எலும்பு, மூட்டு & தசைகள்\n• குழந்தை மருத்துவம் - குழந்தைகள் ஆரோக்கியம்\n• பொதுவான மருத்துவம் - பொதுவான நோய்கள்\n• ICU - முக்கிய பராமரிப்பு\n\nஎந்த துறை பற்றி மேலும் அறிய விரும்புகிறீர்கள்?",
            'hi': "🏥 हमारे अस्पताल के विभाग:\n\n• आपातकालीन - गंभीर और जानलेवा स्थितियां\n• कार्डियोलॉजी - हृदय और हृदय संबंधी मुद्दे\n• न्यूरोलॉजी - मस्तिष्क और तंत्रिका तंत्र\n• ऑर्थोपेडिक्स - हड्डी, जोड़ और मांसपेशियां\n• पेडियाट्रिक्स - बच्चों का स्वास्थ्य\n• सामान्य चिकित्सा - आम बीमारियां\n• ICU - गंभीर देखभाल\n\nआप किस विभाग के बारे में अधिक जानना चाहेंगे?",
            'es': "🏥 Nuestros Departamentos:\n\n• Emergencia - Condiciones críticas y potencialmente mortales\n• Cardiología - Problemas cardíacos y cardiovasculares\n• Neurología - Cerebro y sistema nervioso\n• Ortopédicos - Huesos, articulaciones y músculos\n• Pediatría - Salud infantil\n• Medicina General - Padecimientos comunes\n• UCI - Cuidados críticos\n\n¿Sobre qué departamento le gustaría saber más?",
            'fr': "🏥 Nos Départements:\n\n• Urgences - Conditions critiques et potentiellement mortelles\n• Cardiologie - Problèmes cardiaques et cardiovasculaires\n• Neurologie - Cerveau et système nerveux\n• Orthopédie - Os, articulations et muscles\n• Pédiatrie - Santé des enfants\n• Médecine Générale - Maladies courantes\n• USI - Soins critiques\n\nDe quel département aimeriez-vous en savoir plus?",
            'de': "🏥 Unsere Abteilungen:\n\n• Notaufnahme - Kritische und lebensbedrohliche Zustände\n• Kardiologie - Herz- und Herz-Kreislauf-Probleme\n• Neurologie - Gehirn und Nervensystem\n• Orthopädie - Knochen, Gelenke und Muskeln\n• Pädiatrie - Gesundheit von Kindern\n• Allgemeinmedizin - Häufige Erkrankungen\n• Intensivstation - Kritische Versorgung\n\nÜber welche Abteilung möchten Sie mehr wissen?",
            'zh-cn': "🏥 我们的部门：\n\n• 急诊 - 危重和危及生命的情况\n• 心脏病学 - 心脏和心血管问题\n• 神经学 - 大脑和神经系统\n• 骨科 - 骨骼、关节和肌肉\n• 儿科 - 儿童健康\n• 内科 - 常见疾病\n• ICU - 重症监护\n\n您想了解更多关于哪个部门？"
        }
        return responses.get(lang, responses['en'])
    
    def _get_department_detail(self, dept, lang):
        """Get specific department details"""
        details = {
            'Emergency': {
                'en': "🚑 Emergency Department\n\nHandles: Chest pain, Difficulty breathing, Severe bleeding, Loss of consciousness, Stroke symptoms, Severe trauma\n\nWait Time: 15-30 minutes (based on severity)\n\nStaff: Emergency physicians, Trauma team, Nurses, Paramedics",
                'ta': "🚑 அவசரநடவடிக்கைத் துறை\n\nகையாள்கிறது: நெஞ்சு வலி, சுவாசிப்பதில் சிரமம், கடுமையான இரத்தப்போக்கு, அசையிழப்பு, பக்கவாதம் அறிகுறிகள், கடுமையான காயம்\n\nகாத்திருக்கும் நேரம்: 15-30 நிமிடங்கள்\n\nஊழியர்கள்: அவசர மருத்துவர்கள், ட்ராமா குழு, செவிலியர்கள்",
                'hi': "🚑 आपातकालीन विभाग\n\nसंभालता है: सीने में दर्द, सांस लेने में कठिनाई, गंभीर रक्तस्राव, बेहोशी, स्ट्रोक के लक्षण, गंभीर चोट\n\nप्रतीक्षा समय: 15-30 मिनट\n\nकर्मचारी: आपातकालीन चिकित्सक, ट्रॉमा टीम, नर्स"
            },
            'Cardiology': {
                'en': "❤️ Cardiology Department\n\nHandles: Chest pain, Heart palpitations, Heart attack, High blood pressure, Arrhythmia, Heart failure\n\nWait Time: 20-45 min (emergency), 1-2 weeks (appointment)\n\nStaff: Cardiologists, Cardiac nurses, Technicians",
                'ta': "❤️ இதயவியல் துறை\n\nகையாள்கிறது: நெஞ்சு வலி, இதயத் துடிப்பு, இதய நோய், உயர் ரத்த அழுத்தம், இதய சுருளல், இதய செயலிழப்பு\n\nகாத்திருக்கும் நேரம்: 20-45 நிமிடம் (அவசரம்), 1-2 வாரங்கள் (அபாயண்ட்மென்ட்)\n\nஊழியர்கள்: இதய நிபுணர்கள், இதய செவிலியர்கள்"
            },
            'Neurology': {
                'en': "🧠 Neurology Department\n\nHandles: Headache, Seizures, Stroke, Dizziness, Numbness, Movement disorders\n\nWait Time: 20-40 min (emergency), 1-3 weeks (appointment)\n\nStaff: Neurologists, Neurosurgeons, Nurses",
                'ta': "🧠 நரம்பியல் துறை\n\nகையாள்கிறது: தலைவலி, பிடிப்புகள், பக்கவாதம், தலைசுற்றல், மரத்துப்போதல், இயக்கக் கோளாறுகள்\n\nகாத்திருக்கும் நேரம்: 20-40 நிமிடம் (அவசரம்), 1-3 வாரங்கள் (அபாயண்ட்மென்ட்)\n\nஊழியர்கள்: நரம்பியல் நிபுணர்கள், நரம்பு அறுவைச் சிகிச்சை நிபுணர்கள்"
            },
            'Orthopedics': {
                'en': "🦴 Orthopedics Department\n\nHandles: Fractures, Joint pain, Arthritis, Sports injuries, Back pain\n\nWait Time: 30-60 min (emergency), 1-2 weeks (appointment)\n\nStaff: Orthopedic surgeons, Physiotherapists, Nurses",
                'ta': "🦴 ஆர்தோபெடிக்ஸ் துறை\n\nகையாள்கிறது: முறிவு, மூட்டு வலி, ஆர்த்ரைடிஸ், விளையாட்டு காயங்கள், முதுகு வலி\n\nகாத்திருக்கும் நேரம்: 30-60 நிமிடம் (அவசரம்), 1-2 வாரங்கள் (அபாயண்ட்மென்ட்)\n\nஊழியர்கள்: ஆர்தோபெடிக் அறுவைச் சிகிச்சை நிபுணர்கள்"
            },
            'Pediatrics': {
                'en': "👶 Pediatrics Department\n\nHandles: Childhood illnesses, Vaccinations, Growth monitoring, Developmental issues, Common childhood infections\n\nWait Time: 15-30 min (emergency), 1-2 weeks (appointment)\n\nStaff: Pediatricians, Pediatric nurses, Child specialists",
                'ta': "👶 குழந்தை மருத்துவம் துறை\n\nகையாள்கிறது: குழந்தை நோய்கள், தடுப்பூசிகள், வளர்ச்சி கண்காணிப்பு, வளர்ச்சி சிக்கல்கள், பொதுவான குழந்தை தொற்றுகள்\n\nகாத்திருக்கும் நேரம்: 15-30 நிமிடம் (அவசரம்), 1-2 வாரங்கள் (அபாயண்ட்மென்ட்)\n\nஊழியர்கள்: குழந்தை மருத்துவர்கள்"
            },
            'ICU': {
                'en': "🏥 ICU (Intensive Care Unit)\n\nHandles: Critical illness, Post-surgery recovery, Organ failure, Severe infections, Trauma\n\nWait Time: Immediate admission for critical cases\n\nStaff: Intensivists, ICU nurses, Respiratory therapists",
                'ta': "🏥 ICU (தீவிர சிகிச்சைப் பிரிவு)\n\nகையாள்கிறது: முக்கிய நோய், அறுவைச் சிகிச்சைக்கு பிறகு மீட்பு, அவய்வம் செயலிழப்பு, கடுமையான தொற்றுகள், காயம்\n\nகாத்திருக்கும் நேரம்: முக்கிய வழக்குகளுக்கு உடனடி சேர்க்கை\n\nஊழியர்கள்: தீவிர சிகிச்சை நிபுணர்கள், ICU செவிலியர்கள்"
            }
        }
        
        dept_data = details.get(dept, {})
        return dept_data.get(lang, dept_data.get('en', 'Please contact the hospital for more information.'))
    
    def _get_wait_time(self, lang):
        """Get wait time information"""
        responses = {
            'en': "⏱️ Average Wait Times:\n\n• Emergency: 15-30 minutes\n• Cardiology: 20-45 minutes\n• Neurology: 20-40 minutes\n• Orthopedics: 30-60 minutes\n• General: 30-50 minutes\n\nNote: Wait times may vary based on current patient load.",
            'ta': "⏱️ சராசரி காத்திருக்கும் நேரம்:\n\n• அவசரநடவடிக்கை: 15-30 நிமிடங்கள்\n• இதயவியல்: 20-45 நிமிடங்கள்\n• நரம்பியல்: 20-40 நிமிடங்கள்\n• ஆர்தோபெடிக்ஸ்: 30-60 நிமிடங்கள்\n• பொதுவான: 30-50 நிமிடங்கள்",
            'hi': "⏱️ औसत प्रतीक्षा समय:\n\n• आपातकालीन: 15-30 मिनट\n• कार्डियोलॉजी: 20-45 मिनट\n• न्यूरोलॉजी: 20-40 मिनट\n• ऑर्थोपेडिक्स: 30-60 मिनट\n• सामान्य: 30-50 मिनट"
        }
        return responses.get(lang, responses['en'])
    
    def _get_admission_info(self, lang):
        """Get admission information"""
        responses = {
            'en': "🏥 Patient Admission Process:\n\n1. Complete registration form\n2. Verify insurance/details\n3. Perform triage assessment\n4. Route to appropriate department\n\nOur staff will guide you through each step.",
            'ta': "🏥 நோயாளி சேர்க்கை செயல்முறை:\n\n1. பதிவு படிவத்தை பூர்த்தி செய்க\n2. காப்பீடு/விவரங்களை உறுதிப்படுத்துக\n3. தர排序 மதிப்பீடு செய்க\n4. பொருத்தமான துறைக்கு அனுப்பு"
        }
        return responses.get(lang, responses['en'])
    
    def _get_vitals_info(self, lang):
        """Get vital signs information"""
        responses = {
            'en': "💓 Normal Vital Signs:\n\n• Blood Pressure: <140/90 mmHg\n• Heart Rate: 60-100 bpm\n• Temperature: 98.6°F (37°C)\n• Oxygen Saturation: >95%\n• Pain Level: <3/10\n\nAbnormal vitals require immediate medical attention!",
            'ta': "💓 சாதாரண உயிர் அளவீடுகள்:\n\n• ரத்த அழுத்தம்: <140/90 mmHg\n• இதய வீதம்: 60-100 bpm\n• வெப்பநிலை: 98.6°F (37°C)\n• ஆக்ஸிஜன் செறிவு: >95%\n• வலி நிலை: <3/10"
        }
        return responses.get(lang, responses['en'])
    
    def _get_medication_info(self, lang):
        """Get medication information"""
        responses = {
            'en': "💊 Medication Information:\n\n• Always check patient's medication list in EMR\n• Consult pharmacist for drug interactions\n• Verify dosage with physician\n• Never administer unfamiliar medications\n• Check for allergies first!",
            'ta': "💊 மருந்து தகவல்:\n\n• எப்போதும் EMR-ல் நோயாளி மருந்து பட்டியலை சரிபார்க்க\n• மருந்து ஊடாட்டங்களுக்கு மருந்தாளரை consult செய்க\n• மருத்துவரிடம் dosage உறுதிப்படுத்துக"
        }
        return responses.get(lang, responses['en'])
    
    def _get_visiting_hours(self, lang):
        """Get visiting hours"""
        responses = {
            'en': "👥 Visiting Hours:\n\n• General wards: 10am-8pm (2 visitors)\n• ICU: Restricted (2 visitors, scheduled)\n• Emergency: By staff discretion\n\nMay be restricted during emergencies.",
            'ta': "👥 வருகை நேரங்கள்:\n\n• பொதுவான வார்டுகள்: காலை 10 - இரவு 8 (2 வருகையாளர்கள்)\n• ICU: கட்டுப்படுத்தப்பட்ட\n• அவசர துறை: ஊழியர்களின் விருப்பத்திற்கு உட்பட்ட"
        }
        return responses.get(lang, responses['en'])
    
    def _get_lab_info(self, lang):
        """Get lab information"""
        responses = {
            'en': "🔬 Lab Results Information:\n\n• Check EMR for test results\n• Compare with normal ranges\n• Alert physician if abnormal\n• Results typically available within 24-48 hours",
            'ta': "🔬 ஆய்வு முடிவுகள் தகவல்:\n\n• EMR-ல் ஆய்வு முடிவுகளை சரிபார்க்க\n• சாதாரண வரம்புகளுடன் ஒப்பிடுக\n• இயல்பற்றதாயின் மருத்துவருக்கு தெரிவி"
        }
        return responses.get(lang, responses['en'])
    
    def _get_symptoms_info(self, lang):
        """Get symptoms guidance"""
        responses = {
            'en': "🤒 Common Symptoms & Guidance:\n\n• Chest pain + shortness of breath → Go to Emergency\n• Severe headache + dizziness → Neurology\n• Bone/joint pain → Orthopedics\n• Fever + cough → General Medicine\n• Children's health issues → Pediatrics\n\nFor emergencies, call emergency services immediately!",
            'ta': "🤒 பொதுவான அறிகுறிகள் & வழிகாட்டல்:\n\n• நெஞ்சு வலி + சுவாசிப்பதில் சிரமம் → அவசரநடவடிக்கைக்கு செல்லுங்கள்\n• தலைவலி + தலைசுற்றல் → நரம்பியல்\n• எலும்பு/மூட்டு வலி → ஆர்தோபெடிக்ஸ்\n• காய்ச்சல் + சளி → பொதுவான மருத்துவம்\n• குழந்தைகள் ஆரோக்கிய சிக்கல்கள் → குழந்தை மருத்துவம்"
        }
        return responses.get(lang, responses['en'])
    
    def _get_help_response(self, lang=None):
        """Get help response with suggestions"""
        if lang is None:
            lang = 'en'
        
        responses = {
            'en': "🏥 Hello! I'm your Hospital Assistant. I can help you with:\n\n📋 Questions I can answer:\n• Department information and locations\n• Emergency procedures\n• Wait times and appointments\n• Patient admission process\n• Vital signs information\n• Medication guidance\n• Lab results information\n• Visiting hours\n• Symptom guidance\n\n💬 Just ask me anything! For example:\n- \"What departments do you have?\"\n- \"How long is the wait for cardiology?\"\n- \"What are normal vital signs?\"\n- \"How do I admit a patient?\"\n\n🚨 For emergencies, please call emergency services immediately!",
            'ta': "🏥 வணக்கம்! நான் உங்கள் மருத்துவமனை உதவியாளர். நான் உங்களுக்கு உதவ முடியும்:\n\n📋 நான் பதில் தரக்கூடிய கேள்விகள்:\n• துறை தகவல் மற்று இடங்கள்\n• அவசரநடவடிக்கைகள்\n• காத்திருக்கும் நேரம் மற்று அபாயண்ட்மென்டுகள்\n• நோயாளி சேர்க்கை செயல்முறை\n• உயிர் அளவீடுகள் தகவல்\n• மருந்து வழிகாட்டல்\n• ஆய்வு முடிவுகள் தகவல்\n• வருகை நேரங்கள்\n• அறிகுறி வழிகாட்டல்\n\n💬 வெறுமனே எந்த கேள்வியையும் கேட்குங்கள்!",
            'hi': "🏥 नमस्ते! मैं आपका अस्पताल सहायक हूं। मैं आपकी मदद कर सकता हूं:\n\n📋 मैं जिन सवालों के जवाब दे सकता हूं:\n• विभाग जानकारी और स्थान\n• आपातकालीन प्रक्रियाएं\n• प्रतीक्षा समय और अपॉइंटमेंट\n• रोगी प्रवेश प्रक्रिया\n• जीवन चिह्न जानकारी\n• दवा मार्गदर्शन\n• प्रयोगशाला परिणाम जानकारी\n• मिलने का समय\n• लक्षण मार्गदर्शन\n\n💬 बस कोई भी सवाल पूछो!",
            'es': "🏥 ¡Hola! Soy tu Asistente Hospitalario. Puedo ayudarte con:\n\n📋 Preguntas que puedo responder:\n• Información de departamentos\n• Procedimientos de emergencia\n• Tiempos de espera y citas\n• Proceso de admisión de pacientes\n• Información de signos vitales\n• Guía de medicamentos\n• Información de resultados de laboratorio\n• Horarios de visita\n• Guía de síntomas\n\n💬 ¡Simplemente pregúntame!",
            'fr': "🏥 Bonjour! Je suis votre Assistant Hospitalier. Je peux vous aider avec:\n\n📋 Questions auxquelles je peux répondre:\n• Information sur les départements\n• Procédures d'urgence\n• Temps d'attente et rendez-vous\n• Processus d'admission des patients\n• Information sur les signes vitaux\n• Guide des médicaments\n• Information sur les résultats de laboratoire\n• Heures de visite\n• Guide des symptômes\n\n💬 Demandez-moi simplement!",
            'de': "🏥 Hallo! Ich bin Ihr Krankenhausassistent. Ich kann Ihnen helfen mit:\n\n📋 Fragen, die ich beantworten kann:\n• Abteilungsinformationen\n• Notfallverfahren\n• Wartezeiten und Termine\n• Patientenaufnahmeprozess\n• Vitalzeichen-Informationen\n• Medikamenten-Guide\n• Laborergebnisse-Informationen\n• Besuchszeiten\n• Symptom-Leitfaden\n\n💬 Fragen Sie mich einfach!",
            'zh-cn': "🏥 您好！我是您的医院助理。我可以帮您：\n\n📋 我可以回答的问题：\n• 部门信息和位置\n• 紧急程序\n• 等待时间和预约\n• 患者入院流程\n• 生命体征信息\n• 用药指南\n• 实验室结果信息\n• 探视时间\n• 症状指南\n\n💬 随便问我！"
        }
        return responses.get(lang, responses['en'])
    
    def _get_default_response(self, lang, user_input):
        """Get default response for unrecognized input"""
        responses = {
            'en': "I'm here to help with hospital-related questions. You can ask me about:\n• Departments and their services\n• Emergency procedures\n• Wait times and appointments\n• Patient admission\n• Vital signs information\n• Medications\n• Lab results\n• Visiting hours\n• Symptoms and which department to visit\n\nJust type your question!",
            'ta': "நான் மருத்துவமனை தொடர்பான கேள்விகளுக்கு உதவ இருக்கிறேன். நீங்கள் என்னிடம் கேட்கலாம:\n• துறைகள் மற்று அவற்றின் சேவைகள்\n• அவசரநடவடிக்கைகள்\n• காத்திருக்கும் நேரம் மற்று அபாயண்ட்மென்டுகள்\n• நோயாளி சேர்க்கை\n• உயிர் அளவீடுகள் தகவல்\n• மருந்துகள்\n• ஆய்வு முடிவுகள்\n• வருகை நேரங்கள்\n• அறிகுறிகள் மற்று எந்த துறைக்கு செல்வது\n\nஉங்கள் கேள்வியை தட்டச்சு செய்க!",
            'hi': "मैं अस्पताल से संबंधित सवालों में मदद के लिए हूं। आप मुझसे पूछ सकते हैं:\n• विभाग और उनकी सेवाएं\n• आपातकालीन प्रक्रियाएं\n• प्रतीक्षा समय और अपॉइंटमेंट\n• रोगी प्रवेश\n• जीवन चिह्न जानकारी\n• दवाईयां\n• प्रयोगशाला परिणाम\n• मिलने का समय\n• लक्षण और किस विभाग में जाना है\n\nबस अपना सवाल टाइप करें!",
            'es': "Estoy aquí para ayudar con preguntas relacionadas con el hospital. Puedes preguntarme sobre:\n• Departamentos y sus servicios\n• Procedimientos de emergencia\n• Tiempos de espera y citas\n• Admisión de pacientes\n• Información de signos vitales\n• Medicamentos\n• Resultados de laboratorio\n• Horarios de visita\n• Síntomas y a qué departamento ir\n\n¡Simplemente escribe tu pregunta!",
            'fr': "Je suis là pour aider avec les questions liées à l'hôpital. Vous pouvez me demander:\n• Départements et leurs services\n• Procédures d'urgence\n• Temps d'attente et rendez-vous\n• Admission des patients\n• Information sur les signes vitaux\n• Médicaments\n• Résultats de laboratoire\n• Heures de visite\n• Symptômes et quel département visiter\n\nTapez simplement votre question!",
            'de': "Ich bin hier, um bei krankenhausbezogenen Fragen zu helfen. Sie können mich fragen:\n• Abteilungen und ihre Dienste\n• Notfallverfahren\n• Wartezeiten und Termine\n• Patientenaufnahme\n• Vitalzeichen-Informationen\n• Medikamente\n• Laborergebnisse\n• Besuchszeiten\n• Symptome und welche Abteilung\n\nStellen Sie einfach Ihre Frage!",
            'zh-cn': "我可以帮助您解答医院相关的问题。您可以问我：\n• 部门及其服务\n• 紧急程序\n• 等待时间和预约\n• 患者入院\n• 生命体征信息\n• 药物\n• 实验室结果\n• 探视时间\n• 症状以及应该去哪个部门\n\n直接输入您的问题！"
        }
        return responses.get(lang, responses['en'])
    
    def get_conversation_history(self):
        """Return conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


# Initialize singleton chatbot
_chatbot_instance = None

def get_chatbot():
    """Get or create chatbot instance"""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = HospitalChatbot()
    return _chatbot_instance
