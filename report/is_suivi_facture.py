# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class is_suivi_facture(models.Model):
    _name='is.suivi.facture'
    _description='is.suivi.facture'
    _order='num_facture desc'
    _auto = False

    num_facture   = fields.Char('N°facture')
    date_facture  = fields.Date('Date facture')
    partner_id    = fields.Many2one('res.partner', u'Client')
    total_ht      = fields.Float('Total HT')
    total_ttc     = fields.Float('Total TTC')
    reste_a_payer = fields.Float('Reste à payer')

    def init(self):
        cr=self.env.cr
        tools.drop_view_if_exists(cr, 'is_suivi_facture')
        cr.execute("""
            CREATE OR REPLACE FUNCTION fsens(t text) RETURNS integer AS $$
                    BEGIN

                        IF t = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text]) THEN
                            RETURN -1;
                        ELSE
                            RETURN 1;
                        END IF;

                    END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE view is_suivi_facture AS (
                SELECT 
                    ai.id             as id,
                    ai.invoice_date   as date_facture,
                    ai.name           as num_facture,
                    ai.partner_id     as partner_id,
                    fsens(ai.move_type)*ai.amount_untaxed as total_ht,
                    fsens(ai.move_type)*ai.amount_total   as total_ttc,
                    fsens(ai.move_type)*ai.amount_residual_signed as reste_a_payer
                FROM account_move ai
                WHERE ai.state='posted' and ai.move_type in ('out_invoice', 'out_refund')
                      and ai.invoice_date>='2016-06-01' 
            )
        """)

