from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
)
import torch


class LocalModel():
    """
    TransformerTextSummarizer class is used to generate summary from text.
    This code is inspired by a comment on https://discuss.huggingface.co/t/summarization-on-long-documents/920/21

    Args:
        model_key, huggingface model uri
        language, language of the text
    """

    # TODO looking better summarization models
    # https://huggingface.co/pszemraj/long-t5-tglobal-base-16384-booksum-V11-big_patent-V2?text=Is+a+else+or+outside+the+cob+and+tree+written+being+of+early+client+rope+and+you+have+is+for+good+reasons.+On+to+the+ocean+in+Orange+for+time.+By%27s+the+aggregate+we+can+bed+it+yet.+Why+this+please+pick+up+on+a+sort+is+do+and+also+M+Getoi%27s+nerocos+and+do+rain+become+you+to+let+so+is+his+brother+is+made+in+use+and+Mjulia%27s%27s+the+lay+major+is+aging+Masastup+coin+present+sea+only+of+Oosii+rooms+set+to+you+We+do+er+do+we+easy+this+private+oliiishs+lonthen+might+be+okay.+Good+afternoon+everybody.+Welcome+to+this+lecture+of+Computational+Statistics.+As+you+can+see%2C+I%27m+not+socially+my+name+is+Michael+Zelinger.+I%27m+one+of+the+task+for+this+class+and+you+might+have+already+seen+me+in+the+first+lecture+where+I+made+a+quick+appearance.+I%27m+also+going+to+give+the+tortillas+in+the+last+third+of+this+course.+So+to+give+you+a+little+bit+about+me%2C+I%27m+a+old+student+here+with+better+Bulman+and+my+research+centres+on+casual+inference+applied+to+biomedical+disasters%2C+so+that+could+be+genomics+or+that+could+be+hospital+data.+If+any+of+you+is+interested+in+writing+a+bachelor+thesis%2C+a+semester+paper+may+be+mastathesis+about+this+topic+feel+for+reach+out+to+me.+you+have+my+name+on+models+and+my+email+address+you+can+find+in+the+directory+I%27d+Be+very+happy+to+talk+about+it.+you+do+not+need+to+be+sure+about+it%2C+we+can+just+have+a+chat.+So+with+that+said%2C+let%27s+get+on+with+the+lecture.+There%27s+an+exciting+topic+today+I%27m+going+to+start+by+sharing+some+slides+with+you+and+later+on+during+the+lecture+we%27ll+move+to+the+paper.+So+bear+with+me+for+a+few+seconds.+Well%2C+the+projector+is+starting+up.+Okay%2C+so+let%27s+get+started.+Today%27s+topic+is+a+very+important+one.+It%27s+about+a+technique+which+really+forms+one+of+the+fundamentals+of+data+science%2C+machine+learning%2C+and+any+sort+of+modern+statistics.+It%27s+called+cross+validation.+I+know+you+really+want+to+understand+this+topic+I+Want+you+to+understand+this+and+frankly%2C+nobody%27s+gonna+leave+Professor+Mineshousen%27s+class+without+understanding+cross+validation.+So+to+set+the+stage+for+this%2C+I+Want+to+introduce+you+to+the+validation+problem+in+computational+statistics.+So+the+problem+is+the+following%3A+You+trained+a+model+on+available+data.+You+fitted+your+model%2C+but+you+know+the+training+data+you+got+could+always+have+been+different+and+some+data+from+the+environment.+Maybe+it%27s+a+random+process.+You+do+not+really+know+what+it+is%2C+but+you+know+that+somebody+else+who+gets+a+different+batch+of+data+from+the+same+environment+they+would+get+slightly+different+training+data+and+you+do+not+care+that+your+method+performs+as+well.+On+this+training+data.+you+want+to+to+perform+well+on+other+data+that+you+have+not+seen+other+data+from+the+same+environment.+So+in+other+words%2C+the+validation+problem+is+you+want+to+quantify+the+performance+of+your+model+on+data+that+you+have+not+seen.+So+how+is+this+even+possible%3F+How+could+you+possibly+measure+the+performance+on+data+that+you+do+not+know+The+solution+to%3F+This+is+the+following+realization+is+that+given+that+you+have+a+bunch+of+data%2C+you+were+in+charge.+You+get+to+control+how+much+that+your+model+sees.+It+works+in+the+following+way%3A+You+can+hide+data+firms+model.+Let%27s+say+you+have+a+training+data+set+which+is+a+bunch+of+doubtless+so+X+eyes+are+the+features+those+are+typically+hide+and+national+vector.+It%27s+got+more+than+one+dimension+for+sure.+And+the+why+why+eyes.+Those+are+the+labels+for+supervised+learning.+As+you%27ve+seen+before%2C+it%27s+the+same+set+up+as+we+have+in+regression.+And+so+you+have+this+training+data+and+now+you+choose+that+you+only+use+some+of+those+data+to+fit+your+model.+You%27re+not+going+to+use+everything%2C+you+only+use+some+of+it+the+other+part+you+hide+from+your+model.+And+then+you+can+use+this+hidden+data+to+do+validation+from+the+point+of+you+of+your+model.+This+hidden+data+is+complete+by+unseen.+In+other+words%2C+we+solve+our+problem+of+validation.

    def __init__(self, model_key='facebook/bart-large-cnn', language='en'):
        self._tokenizer = AutoTokenizer.from_pretrained(model_key)

        self._language = language

        self._model = AutoModelForSeq2SeqLM.from_pretrained(model_key)

        self._device = "cuda:0" if torch.cuda.is_available() else "cpu"

    def __chunk_text(self, paragraphs) -> list:
        """Generate chunk of tokens from a list of paragrams.

        Args:
            paragraphs (list): list of text paragrams

        Return: 
            chunks (list): list of text paragrams
        """

        chunks = []
        chunk = ''
        length = 0

        for paragraph in paragraphs:
            tokenized_sentence = self._tokenizer.encode(
                paragraph, truncation=False, max_length=None, return_tensors='pt')[0]

            if len(tokenized_sentence) > self._tokenizer.model_max_length:
                continue

            length += len(tokenized_sentence)

            if length <= self._tokenizer.model_max_length:
                chunk = chunk + ' ' + paragraph
            else:
                chunks.append(chunk.strip())
                chunk = paragraph
                length = len(tokenized_sentence)

        if len(chunk) > 0:
            chunks.append(chunk.strip())

        return chunks

    def __clean_text(self, text):
        if text.count('.') == 0:
            return text.strip()

        end_index = text.rindex('.') + 1

        return text[0: end_index].strip()

    def __call__(self, paragraphs: list, beams=5, summary_length='full', *args, **kwargs) -> list[str]:
        """Summarize text.

        Args:
            paragraphs (list)): list of text paragrams to be summarized
            beams (int): number of beams to use for the generation of the summary
            summary_length (str): length of the summary, can be 'full' or 'first_chunk'

        Return:
            summaries (list): list of summaries
        """

        chunk_texts = self.__chunk_text(paragraphs)
        chunk_summaries = []

        for chunk_text in chunk_texts:

            if (summary_length == 'first_chunk' and len(chunk_summaries) > 0):
                break

            input_tokenized = self._tokenizer.encode(
                chunk_text, return_tensors='pt')

            input_tokenized = input_tokenized.to(self._device)

            summary_ids = self._model.to(self._device).generate(
                input_tokenized,
                length_penalty=3.0,
                min_length=int(0.1 * len(chunk_text)),
                max_length=int(0.2 * len(chunk_text)),
                early_stopping=True,
                num_beams=beams,
                no_repeat_ngram_size=2)

            output = [self._tokenizer.decode(
                g, skip_special_tokens=True, clean_up_tokenization_spaces=True) for g in summary_ids]

            chunk_summaries.append(output)

        summaries = [self.__clean_text(
            text) for chunk_summary in chunk_summaries for text in chunk_summary]

        return summaries
