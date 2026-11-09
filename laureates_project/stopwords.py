"""
Здесь сохранен список английских стоп-слов 
для анализа текстов мотиваций.

Стоп-слова - это часто встречающиеся слова, которые обычно
не несут самостоятельной смысловой нагрузки (артикли, предлоги, 
местоимения и вспомогательные глаголы).

При анализе мотиваций Нобелевских премий такие слова могут занимать 
первые места в частотном рейтинге, хотя сами по себе мало говорят о 
причинах награждения.

Поэтому после первоначального подсчёта частот мы исключаем слова из 
STOPWORDS и повторяем анализ.
"""

STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'also', 'an',
    'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before',
    'being', 'below', 'between', 'both', 'but', 'by', 'can', 'could', 'did',
    'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers',
    'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is',
    'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no',
    'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our',
    'ours', 'ourselves', 'out', 'over', 'own', 's', 'same', 'she', 'should',
    'so', 'some', 'such', 't', 'than', 'that', 'the', 'their', 'theirs',
    'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those',
    'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we',
    'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why',
    'will', 'with', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves',
}
