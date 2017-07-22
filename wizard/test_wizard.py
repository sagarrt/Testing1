# -*- coding: utf-8 -*-
# copyright reserved

from openerp import models, fields, api


class QualityScrapDoc(models.TransientModel):
    """This wizard is used to preset the test for a given
    inspection. This will fill in the 'test' field, but will
    also fill in all lines of the inspection with the corresponding lines of
    the template.
    """
    _name = 'quality.scrap.doc'

    test = fields.Many2one(comodel_name='quality.test', string='Test')
    uploaded_documents = fields.Many2many('ir.attachment','wizard_attachment_rel','wizard','id','Scrap Documents')
    
    @api.multi
    def action_upload_document(self):
    	self.ensure_one()
    	if not self.uploaded_documents:
    		raise exceptions.Warning(_("Please Upload at least one Document of Quality Check Failed"))
        inspection = self.env['quality.inspection'].browse(self.env.context['active_id'])
        inspection.uploaded_documents = self.uploaded_documents
        
        inspection.action_do_confirm()
