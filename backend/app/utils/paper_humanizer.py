import re
import random
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class PaperHumanizer:
    """
    Utility class to humanize AI-generated academic content,
    making it sound more natural and less robotic.
    """
    
    def __init__(self):
        # Transition phrases for better flow
        self.transitions = {
            'addition': [
                "Furthermore,", "Additionally,", "Moreover,", "In addition,",
                "Besides that,", "What's more,", "On top of that,", "Beyond this,"
            ],
            'contrast': [
                "However,", "Nevertheless,", "On the other hand,", "In contrast,",
                "Despite this,", "Alternatively,", "Yet,", "Nonetheless,"
            ],
            'consequence': [
                "As a result,", "Consequently,", "Therefore,", "Thus,",
                "Hence,", "For this reason,", "Accordingly,", "Subsequently,"
            ],
            'emphasis': [
                "Indeed,", "Certainly,", "Clearly,", "Obviously,", "Without doubt,",
                "Importantly,", "Notably,", "Particularly,", "Especially,"
            ],
            'example': [
                "For instance,", "As an example,", "To illustrate,", "Specifically,",
                "For example,", "In particular,", "Consider that,", "Take for example,"
            ]
        }
        
        # Academic vocabulary alternatives to make text less repetitive
        self.synonyms = {
            'shows': ['demonstrates', 'reveals', 'indicates', 'suggests', 'illustrates', 'exhibits'],
            'important': ['significant', 'crucial', 'vital', 'essential', 'key', 'fundamental'],
            'different': ['distinct', 'varied', 'diverse', 'alternative', 'unique', 'separate'],
            'method': ['approach', 'technique', 'strategy', 'procedure', 'methodology', 'process'],
            'result': ['outcome', 'finding', 'conclusion', 'consequence', 'effect', 'product'],
            'problem': ['challenge', 'issue', 'difficulty', 'concern', 'obstacle', 'matter'],
            'solution': ['resolution', 'approach', 'answer', 'remedy', 'fix', 'way forward'],
            'use': ['utilize', 'employ', 'apply', 'implement', 'leverage', 'adopt'],
            'improve': ['enhance', 'optimize', 'refine', 'upgrade', 'advance', 'better'],
            'create': ['develop', 'generate', 'establish', 'produce', 'construct', 'build']
        }
        
        # Common robotic patterns to avoid or rephrase
        self.robotic_patterns = [
            r'\b(?:This paper|The paper|This study|This research)\b',
            r'\bIn conclusion,\b',
            r'\bIn summary,\b',
            r'\bIt is important to note that\b',
            r'\bIt should be noted that\b'
        ]
        
        # Sentence starters to add variety
        self.sentence_starters = [
            "Given that", "Considering", "Since", "Because", "While", "Although",
            "Despite", "Through", "By examining", "Upon investigation", "When analyzing"
        ]
    
    async def humanize_content(self, content: str, section_type: str) -> str:
        """
        Main method to humanize AI-generated content
        
        Args:
            content: The content to humanize
            section_type: Type of section (abstract, introduction, etc.)
            
        Returns:
            Humanized content
        """
        try:
            # Basic cleanup
            humanized = content.strip()
            
            # Split into paragraphs for easier processing
            paragraphs = humanized.split('\n\n')
            
            # Process each paragraph
            processed_paragraphs = []
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip():
                    processed = self._process_paragraph(paragraph.strip(), i, section_type)
                    processed_paragraphs.append(processed)
            
            # Rejoin paragraphs
            humanized = '\n\n'.join(processed_paragraphs)
            
            # Final polishing
            humanized = self._final_polish(humanized, section_type)
            
            return humanized
            
        except Exception as e:
            logger.error(f"Error in humanization: {str(e)}")
            return content  # Return original content if humanization fails
    
    def _process_paragraph(self, paragraph: str, paragraph_index: int, section_type: str) -> str:
        """Process a single paragraph for humanization"""
        # Split into sentences
        sentences = self._split_into_sentences(paragraph)
        
        processed_sentences = []
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                processed = self._process_sentence(sentence.strip(), i, paragraph_index, section_type)
                processed_sentences.append(processed)
        
        # Add transitions between sentences if needed
        if len(processed_sentences) > 1:
            processed_sentences = self._add_transitions(processed_sentences, section_type)
        
        return ' '.join(processed_sentences)
    
    def _process_sentence(self, sentence: str, sentence_index: int, paragraph_index: int, section_type: str) -> str:
        """Process a single sentence"""
        # Avoid repetitive sentence starters
        if paragraph_index > 0 and sentence_index == 0 and len(sentence.split()) > 5:
            sentence = self._vary_sentence_starter(sentence)
        
        # Replace repetitive words with synonyms
        sentence = self._replace_synonyms(sentence)
        
        # Fix robotic patterns
        sentence = self._fix_robotic_patterns(sentence)
        
        # Ensure proper punctuation
        if not sentence.endswith(('.', '!', '?', ':')):
            sentence += '.'
        
        return sentence
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - can be improved with more sophisticated methods
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _vary_sentence_starter(self, sentence: str) -> str:
        """Add variety to sentence starters"""
        # Don't change every sentence, just occasionally
        if random.random() < 0.3:  # 30% chance
            starter = random.choice(self.sentence_starters)
            # Convert first word to lowercase and add starter
            first_word = sentence.split()[0].lower()
            rest = ' '.join(sentence.split()[1:])
            return f"{starter} {first_word} {rest}"
        return sentence
    
    def _replace_synonyms(self, sentence: str) -> str:
        """Replace repetitive words with synonyms"""
        words = sentence.split()
        result = []
        
        for word in words:
            word_lower = word.lower().rstrip('.,!?:;')
            if word_lower in self.synonyms and random.random() < 0.4:  # 40% chance
                synonym = random.choice(self.synonyms[word_lower])
                # Preserve capitalization
                if word[0].isupper():
                    synonym = synonym.capitalize()
                # Preserve punctuation
                punctuation = word[len(word.rstrip('.,!?:;')):]
                result.append(synonym + punctuation)
            else:
                result.append(word)
        
        return ' '.join(result)
    
    def _fix_robotic_patterns(self, sentence: str) -> str:
        """Replace or modify robotic patterns"""
        replacements = {
            r'\bThis paper\b': 'Our research',
            r'\bThe paper\b': 'This work',
            r'\bThis study\b': 'Our investigation',
            r'\bThis research\b': 'The present study',
            r'\bIt is important to note that\b': 'Notably,',
            r'\bIt should be noted that\b': 'We observe that',
            r'\bIn conclusion,\b': 'To summarize,',
            r'\bIn summary,\b': 'Overall,'
        }
        
        result = sentence
        for pattern, replacement in replacements.items():
            if random.random() < 0.7:  # 70% chance of replacement
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def _add_transitions(self, sentences: List[str], section_type: str) -> List[str]:
        """Add transitions between sentences for better flow"""
        result = [sentences[0]]  # Keep first sentence as is
        
        for i in range(1, len(sentences)):
            sentence = sentences[i]
            
            # Add transitions occasionally (not to every sentence)
            if random.random() < 0.3 and not self._already_has_transition(sentence):
                transition_type = self._determine_transition_type(sentences[i-1], sentence, section_type)
                if transition_type:
                    transition = random.choice(self.transitions[transition_type])
                    sentence = f"{transition} {sentence}"
            
            result.append(sentence)
        
        return result
    
    def _already_has_transition(self, sentence: str) -> bool:
        """Check if sentence already starts with a transition"""
        first_word = sentence.split()[0].lower().rstrip(',')
        transition_words = [word.lower().rstrip(',') for transition_list in self.transitions.values() 
                           for word in transition_list]
        return first_word in transition_words
    
    def _determine_transition_type(self, prev_sentence: str, current_sentence: str, section_type: str) -> Optional[str]:
        """Determine what type of transition to use"""
        # Simple heuristic-based approach
        if 'however' in current_sentence.lower() or 'but' in current_sentence.lower():
            return None  # Already has contrast
        elif 'therefore' in current_sentence.lower() or 'thus' in current_sentence.lower():
            return None  # Already has consequence
        elif section_type == 'results' or section_type == 'discussion':
            # In results/discussion, often add examples or emphasis
            return random.choice(['example', 'emphasis'])
        elif section_type == 'conclusion':
            return 'consequence'
        else:
            return random.choice(['addition', 'contrast'])
    
    def _final_polish(self, content: str, section_type: str) -> str:
        """Apply final polishing touches"""
        # Ensure proper spacing
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        # Fix double punctuation
        content = re.sub(r'[.]{2,}', '.', content)
        content = re.sub(r'[,]{2,}', ',', content)
        
        # Ensure proper paragraph breaks
        paragraphs = content.split('\n\n')
        
        # Section-specific formatting
        if section_type == 'references':
            content = self._format_references(content)
        elif section_type == 'abstract':
            content = self._format_abstract(content)
        
        return content
    
    def _format_references(self, content: str) -> str:
        """Format references section"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip() and not line.startswith('['):
                # Add proper IEEE formatting if missing
                formatted_lines.append(line.strip())
            elif line.strip():
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_abstract(self, content: str) -> str:
        """Format abstract section"""
        # Ensure abstract is a single paragraph
        content = ' '.join(content.split('\n'))
        return content
    
    def get_humanization_stats(self, original: str, humanized: str) -> Dict[str, int]:
        """Get statistics about the humanization process"""
        return {
            'original_word_count': len(original.split()),
            'humanized_word_count': len(humanized.split()),
            'original_sentence_count': len(self._split_into_sentences(original)),
            'humanized_sentence_count': len(self._split_into_sentences(humanized)),
            'changes_made': 1 if original != humanized else 0
        }