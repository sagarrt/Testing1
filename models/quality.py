# -*- coding: utf-8 -*-
# copyright reserved

from openerp import models, fields, api, exceptions, _

class QualityChecking(models.Model):
    _name = 'quality.checking'
    _description = "Quality Check for all MO and PO"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "id desc"
    
    @api.one
    def _get_qty(self):
    	qty=approved=reject=0
    	for rec in self.quality_line:
		qty += rec.quantity
	for rec1 in self.history_line_approve:
		approved += rec1.quantity
	for rec2 in self.history_line_reject:
		reject += rec2.quantity
	self.quantity = qty
	self.approved_qty =approved
	self.reject_qty = reject
    
    @api.one
    @api.depends('quantity','mo_state','quality_line','history_line_reject','history_line_reject.move_status')
    def _get_state(self):
	if self.quantity:
		self.state='available'
	elif self.mo_state == 'in_production':
		self.state='waiting'
	elif self.mo_state == 'done':
		flag=True
		for rec in self.history_line_reject:
			print "66666666",rec.move_status
			if rec.move_status in ('in_mo','in_po'):
				flag=False
				self.state='waiting' 
		if flag:
			self.state='complete' 
    		
    name = fields.Char('Name', required=True, readonly=True)
    quality_line=fields.One2many('quality.checking.line','quality_id','Quality Line') 
    history_line_approve=fields.One2many('quality.checking.line.history','quality_id','Quality Line History',domain=[('state','=','approve')])
    history_line_reject=fields.One2many('quality.checking.line.history','quality_id','Quality Line History',domain=[('state','=','reject')]) 
    source = fields.Char('Source', required=True, readonly=True)
    picking_id = fields.Many2one("stock.picking",'QC Operation',readonly=True)
    mrp_id = fields.Many2one("mrp.production",'MO Number',readonly=True)
    purchase_id = fields.Many2one("purchase.order",'PO Number',readonly=True)
    
    product_id = fields.Many2one("product.product")
    uom_id = fields.Many2one("product.uom",readonly=True)
    quantity = fields.Float(string="Quantity Available", compute="_get_qty")
    approved_qty = fields.Float(string="Approved Qty",compute="_get_qty")
    reject_qty = fields.Float(string="Reject Qty",compute="_get_qty")
    state = fields.Selection([('draft', 'Draft'),
				 ('waiting', 'Waiting Quantity'),
				 ('available', 'Available'),
				 ('complete', 'Complete'),
				 ('canceled', 'Canceled')],
				string='State',compute="_get_state",store=True)
				
    mo_state = fields.Selection([('draft', 'New'), ('cancel', 'Cancelled'), ('confirmed', 'Awaiting Raw Materials'),
                ('ready', 'Ready to Produce'), ('in_production', 'Production Started'), ('done', 'Done')],
            string='MO Status', readonly=True,related="mrp_id.state")
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
        	default=lambda self: self.env['res.company']._company_default_get('quality.checking'))
    user = fields.Many2one('res.users', string='Responsible',track_visibility='always', default=lambda self: self.env.user)
    
     
    @api.model
    def create(self,vals):
    	vals.update({'name':self.env['ir.sequence'].next_by_code('quality.checking')})
    	return super(QualityChecking,self).create(vals)
    
    @api.multi
    def quality_test(self):
    	context=self._context.copy()
    	qty= context.get('qty') if context.get('qty') else self.quantity
    	if not context.get('qty'):
    	    search_id= self.env['quality.inspection'].search([('quality_id','=',self.id),('state','in',('draft','ready'))])
    	    if search_id:
    		raise exceptions.Warning(_("Already inspection is running on this Request Please complete That."))
    	if not qty:
    		raise exceptions.Warning(_("No Quantity Available To Perform Quality Test"))
    	full = False if context.get('default_quality_line_id') else True
    	context.update({'default_name':'New','default_product':self.product_id.id,
    			'default_qty':qty,'default_quality_id':self.id,'default_full_test':full})
    	form_id = self.env.ref('quality_control.quality_inspection_form_view')
    	return {
		'name' :'Perform New Test',
		'type': 'ir.actions.act_window',
		'view_type': 'form',
		'view_mode': 'form',
		'res_model': 'quality.inspection',
		'views': [(form_id.id, 'form')],
		'view_id': form_id.id,
		'target': 'new',
		'context':context,
		'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
	    }
	    
    @api.multi
    def open_test_performed(self):
    	tree_id = self.env.ref('quality_control.quality_inspection_tree_view')
    	form_id = self.env.ref('quality_control.quality_inspection_form_view')
    	if self._context.get('quality_line_id'):
    		domain=[('quality_line_id','=',self._context.get('quality_line_id'))]
	else:
		domain=[('quality_id','=',self.id)]
    	return {
		'name' :'Open Inspections',
		'type': 'ir.actions.act_window',
		'view_type': 'form',
		'view_mode': 'tree',
		'res_model': 'quality.inspection',
		'views': [(tree_id.id,'tree'),(form_id.id, 'form')],
		'view_id': tree_id.id,
		'target': 'new',
		'domain':domain,
	    }
    	
    	
class QualityCheckingLine(models.Model):
    _name = 'quality.checking.line'
    _description = "when every time MO produce some quantity it added to quality check"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name="lot_id"
    _order = "id desc"
    
    @api.one
    def _get_quantity(self):
    	approved=reject=0
    	for rec in self.history_line_approve:
		approved += rec.quantity
	for rec1 in self.history_line_reject:
		reject += rec1.quantity
	self.approved_qty =approved
	self.reject_qty = reject

    name = fields.Char('Name',readonly=True)
    quality_id = fields.Many2one("quality.checking",readonly=True)
    product_id = fields.Many2one("product.product",readonly=True)
    quantity = fields.Float(string="Available Qty", default=1.0,readonly=True)
    uom_id = fields.Many2one("product.uom",readonly=True)
    approved_qty = fields.Float(string="Approve Qty",compute='_get_quantity')
    reject_qty = fields.Float(string="Reject Qty", compute='_get_quantity')
    state = fields.Selection([('draft', 'Draft'),('available', 'Available'),
				 ('complete', 'Complete'),
				 ('canceled', 'Canceled')],
				string='State', readonly=True, default='draft')
    n_type = fields.Selection([('new', 'New Production'),('repaired', 'Repaired')], string='Quantity From', readonly=True, default='new')
    lot_id = fields.Many2one('stock.production.lot', 'LOT Number',readonly=True)			
    mo_state = fields.Selection(
            [('draft', 'New'), ('cancel', 'Cancelled'), ('confirmed', 'Awaiting Raw Materials'),
                ('ready', 'Ready to Produce'), ('in_production', 'Production Started'), ('done', 'Done')],
            string='MO Status', readonly=True, default='draft')
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
        	default=lambda self: self.env['res.company']._company_default_get('quality.checking'))
    history_line_approve=fields.One2many('quality.checking.line.history','quality_line_id','Quality Line History',domain=[('state','=','approve')])
    history_line_reject=fields.One2many('quality.checking.line.history','quality_line_id','Quality Line History',domain=[('state','=','reject')])   
    scrap_reason = fields.Selection([('reject','Quality not Good'),('min','Quantity is Less' )], string="Scrap Reason")
    
         
    @api.multi
    def quality_test(self):	# perform new test
    	search_id= self.env['quality.inspection'].search([('quality_line_id','=',self.id),('state','in',('draft','ready'))])
    	if search_id:
    		raise exceptions.Warning(_("Already inspection is running on this Request Please complete That."))
	search_main_id= self.env['quality.inspection'].search([('quality_id','=',self.quality_id.id),('state','in',('draft','ready')),('quality_line_id','=',False)])
    	if search_main_id:
    		raise exceptions.Warning(_("Already inspection is running on this Request Please complete That."))
    	return self.with_context(qty=self.quantity,default_quality_line_id=self.id).quality_id.quality_test()  # use Parent Method

    @api.multi
    def open_test_performed(self):	#show all test
    	return self.with_context(quality_line_id=self.id).quality_id.open_test_performed()
	    


