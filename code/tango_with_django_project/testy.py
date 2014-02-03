# This file is for testing random simple functions

def decode_url(url):
    ''' Takes string and either removes or places underscores to toggle between URL or plain text.
        str -> str
        
        decode_url('test_url') -> 'test url'
        decode_url('test url') -> 'test_url'
    '''
    if '_' in url:
        return url.replace('_',' ')
    else:
        return url.replace(' ','_')
    

def commas(string, comma_string=''):
    comma_string = string[-3:]+comma_string
    if len(string) <= 3:
        return comma_string
    else:
        return commas(string[0:-3], ','+comma_string)
