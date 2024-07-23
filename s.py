class String:
    @staticmethod
    def screaming_snake_to_camel(s: str) -> str:
        return ''.join([
            w.capitalize() for w in s.split('_')
        ])
        
