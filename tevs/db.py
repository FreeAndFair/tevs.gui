try:
    import psycopg2 as DB
    DatabaseError = DB.DatabaseError
except ImportError:
    DatabaseError = Exception
    pass

import pdb
class NullDB(object):
    def __init__(self, *_):
        pass
    def close(self):
        pass
    def insert(self, _):
        pass


class PostgresDB(object):
    def __init__(self, name, user):
        self.conn = DB.connect(database=name, user=user)

    def close(self):
        try:
            self.conn.close()
        except DatabaseError: 
            pass

    def query(self, q, *a):
        "returns a list of all results of q parameterized with a"
        cur = self.conn.cursor()
        cur.execute(q, *a)
        r = list(cur)
        cur.close()
        return r

    def query1(self, q, *a):
        "return one result from q parameterized with a"
        cur = self.conn.cursor()
        cur.execute(q, *a)
        r = cur.fetchone()
        cur.close()
        return r

    def insert(self, ballot):
        #NB all db queries are decalred as strings after the method body for
        #clarity

        #XXX we should not have to chop it off to an arbitary and small length
        if type(ballot.pages[0]) != tuple:
            try:
                search_key = ballot.pages[0].template.barcode
            except TypeError, IndexError:
                search_key = "$".join(p.template.barcode for p in ballot.pages)
                
            name1 = ballot.pages[0].filename
            name2 = "<No such file>"
            if len(ballot.pages) > 1:
                name2 = ballot.pages[1].filename
        else:
            try:
                search_key = ballot.pages[0].template.barcode
            except TypeError, IndexError:
                search_key = "$".join(p[0].template.barcode for p in ballot.pages)
            b = ballot.pages[0]
            name1, name2 = b[0].filename, b[1].filename

        cur = self.conn.cursor()

        # create a record for this ballot

        cur.execute(_pg_mk, (search_key, name1, name2))
        sql_ret = cur.fetchall()

        try:
            ballot_id = int(sql_ret[0][0])
        except ValueError as e:
            self.conn.rollback()
            raise DatabaseError("Corrupt ballot_id")

        # write each result into our record

        for vd in ballot.results:
            try:
                cur.execute(_pg_ins, (
                        ballot_id,
                        vd.contest[:80],
                        vd.choice[:80],

                        vd.coords[0],
                        vd.coords[1],
                        vd.stats.adjusted.x,
                        vd.stats.adjusted.y, 

                        vd.stats.red.intensity,
                        vd.stats.red.darkest_fourth,
                        vd.stats.red.second_fourth,
                        vd.stats.red.third_fourth,
                        vd.stats.red.lightest_fourth,

                        vd.stats.green.intensity,
                        vd.stats.green.darkest_fourth,
                        vd.stats.green.second_fourth,
                        vd.stats.green.third_fourth,
                        vd.stats.green.lightest_fourth,

                        vd.stats.blue.intensity,
                        vd.stats.blue.darkest_fourth,
                        vd.stats.blue.second_fourth,
                        vd.stats.blue.third_fourth,
                        vd.stats.blue.lightest_fourth,

                        vd.was_voted, 
                        vd.ambiguous,
                        vd.filename
                    )
                )
            except:
                self.conn.rollback()
                raise


        self.conn.commit()

_pg_mk = """INSERT INTO ballots (
            processed_at, 
            code_string, 
            file1,
            file2
        ) VALUES (now(), %s, %s, %s) RETURNING ballot_id ;"""

_pg_ins = """INSERT INTO voteops (
            ballot_id,
            contest_text,
            choice_text,

            original_x,
            original_y,
            adjusted_x,
            adjusted_y,

            red_mean_intensity,
            red_darkest_pixels,
            red_darkish_pixels,
            red_lightish_pixels,
            red_lightest_pixels,

            green_mean_intensity,
            green_darkest_pixels,
            green_darkish_pixels,
            green_lightish_pixels,
            green_lightest_pixels,

            blue_mean_intensity,
            blue_darkest_pixels,
            blue_darkish_pixels,
            blue_lightish_pixels,
            blue_lightest_pixels,

            was_voted, 
            suspicious,
            filename
        ) VALUES (
            %s, %s, %s,  
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, 
            %s, 
            %s, 
            %s
        )"""
