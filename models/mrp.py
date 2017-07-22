# -*- coding: utf-8 -*-
# copyright reserved

from openerp.osv import fields, osv
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp

    	
class MrpProduction(models.Model):
    _inherit='mrp.production'
   
    @api.multi
    def action_produce(self, production_qty, production_mode, wiz=False):
    	production_id = self._context.get('active_id') if self._context.get('active_id') else self.id
    	lot_id = self._context.get('lot_id') if self._context.get('lot_id') else False
    	picking_id=False
    	for move in self.move_created_ids:
    		picking_id=move.move_dest_id.picking_id.id
    	for rec in self:
    	    search_id=self.env['quality.checking'].search([('source','=',rec.name)])
    	    if not search_id:
    		vals={'source':rec.name,'product_id':rec.product_id.id,'mrp_id':rec.id,'picking_id':picking_id,
    			'quality_line':[(0,0,{'name':rec.name,'quantity':production_qty,'mo_state':rec.state,
    				'product_id':rec.product_id.id,'uom_id':rec.product_uom.id,'lot_id':lot_id,
				'state':'available','n_type':'new'})],'uom_id':rec.product_uom.id}
    		self.env['quality.checking'].create(vals)
            else:
            	vals={'quality_line':[(0,0,{'name':rec.name,'quantity':production_qty,'mo_state':rec.state,
            		'product_id':rec.product_id.id,'uom_id':rec.product_uom.id,'lot_id':lot_id,'state':'available',
            			'n_type':'new'})]}
            	search_id.write(vals)
    	return super(MrpProduction, self).action_produce(production_qty, production_mode, wiz)
    	
    	
class mrp_product_produce(osv.osv_memory):
    _inherit = "mrp.product.produce"
   
    @api.v7
    def do_produce(self, cr, uid, ids, context=None):
        production_id = context.get('active_id', False)
        assert production_id, "Production Id should be specified in context as a Active ID."
        data = self.browse(cr, uid, ids[0], context=context)
        context.update({'lot_id':data.lot_id.id})
        self.pool.get('mrp.production').action_produce(cr, uid, production_id,
                            data.product_qty, data.mode, data, context=context)
        return {}

class QualityCheckingHistory(models.Model):
    _name = 'quality.checking.line.history'
    _description = "store history of every quality checking in ERP"
    _rec_name='mrp_id'

    quality_id = fields.Many2one("quality.checking",readonly=True)
    quality_line_id = fields.Many2one("quality.checking.line",readonly=True)
    inspection_id = fields.Many2one('quality.inspection', string='Inspection')
    product_id = fields.Many2one("product.product",readonly=True)
    quantity = fields.Float(string="Quantity Available", default=1.0,readonly=True)
    uom_id = fields.Many2one("product.uom",readonly=True)
    state = fields.Selection([('approve', 'Approve'),('reject', 'Reject')], string='State', readonly=True)
    nstate = fields.Selection([('draft', 'Draft'),('done', 'Done')], string='State',default='draft', readonly=True)
    move_status = fields.Selection([('in_mo', 'Return To MO'),('move_scrap', 'Move To scrap'),('partial','Partial Move'),('move_quality', 'Move To Quality'),('in_po','Return to PO'),('done','Done')], string='Status', readonly=True)
    mrp_id = fields.Many2one("mrp.production",'MO Number',related='quality_id.mrp_id',store=True,readonly=True)
    lot_id = fields.Many2one('stock.production.lot', 'LOT Number',related='quality_line_id.lot_id',store=True,readonly=True)
    approve_qty = fields.Float("Send TO Quality", default=0)
    reject_qty = fields.Float("Send TO Scrap", default=0)
    history_line=fields.One2many('quality.checking.line.history.line','history_id','History Line') 
    
    @api.multi
    def open_inspection(self):
    	form_id = self.env.ref('quality_control.quality_inspection_form_view')
    	return {
		'name' :'Perform New Test',
		'type': 'ir.actions.act_window',
		'view_type': 'form',
		'view_mode': 'form',
		'res_model': 'quality.inspection',
		'views': [(form_id.id, 'form')],
		'view_id': form_id.id,
		'res_id':self.inspection_id.id,
		'target': 'new',
	    }
    
    @api.multi
    def action_validate(self):
    	for rec in self:
    		if (rec.approve_qty+rec.reject_qty) > rec.quantity :
    			raise exceptions.Warning(_("(Send to Quality + Send TO Scrap) shoud be equal to Quantity Available"))
    		if rec.approve_qty <0.0 :
    			raise exceptions.Warning(_("Please Enter proper Quantity in Send to Quality"))
		if not rec.approve_qty and not rec.reject_qty:
			raise exceptions.Warning(_("Please Enter Value in Send to Quality or Send TO Scrap"))
		if (rec.approve_qty+rec.reject_qty) <= rec.quantity:
			if rec.approve_qty:
				rec.history_line=[(0,0,{'product_id':rec.product_id.id,'quantity':rec.approve_qty,
						'status':'move_quality'})]
				rec.quality_id.quality_line=[(0,0,{'name':rec.mrp_id.name,'quantity':rec.approve_qty,
	    			'product_id':rec.product_id.id,'uom_id':rec.uom_id.id,'lot_id':rec.lot_id.id,
	    			'state':'available','n_type':'repaired'})]
			if rec.reject_qty:
				rec.history_line=[(0,0,{'product_id':rec.product_id.id,'quantity':rec.reject_qty,
						'status':'move_scrap'})]
		if rec.approve_qty == rec.quantity:
	    		rec.state='move_quality'
    		elif rec.reject_qty == rec.quantity:
	    		rec.state='move_scrap'
    		else:
    			 rec.state = 'partial'
    	return True
    	

class QualityCheckingHistoryLine(models.Model):
    _name = 'quality.checking.line.history.line'
    _description = "store history of every record in rejection from MO Scrap"

    history_id = fields.Many2one("quality.checking.line.history",readonly=True)
    product_id = fields.Many2one("product.product",readonly=True)
    quantity = fields.Float(string="Quantity Available", default=1.0,readonly=True)
    status = fields.Selection([('move_scrap', 'Move To scrap'),('move_quality', 'Move To Quality')], string='Status', readonly=True)
    
    
    
