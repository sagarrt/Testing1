# -*- coding: utf-8 -*-
# copyright reserved

from datetime import date, datetime,timedelta
from dateutil import relativedelta
import json
import time
import sets

import openerp
from openerp.osv import fields, osv
from openerp.tools.float_utils import float_compare, float_round
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import SUPERUSER_ID, api, models
import openerp.addons.decimal_precision as dp
from openerp.addons.procurement import procurement
import logging
from openerp.exceptions import UserError
    	
class stock_move(osv.osv):
    _inherit='stock.move'
            
 #CH_N111 add code to get seperate Quality Check for each MO
    @api.cr_uid_ids_context
    def _picking_assign(self, cr, uid, move_ids, context=None):
        """Try to assign the moves to an existing picking
        that has not been reserved yet and has the same
        procurement group, locations and picking type  (moves should already have them identical)
         Otherwise, create a new picking to assign them to.
        """
        move = self.browse(cr, uid, move_ids, context=context)[0]
        pick_obj = self.pool.get("stock.picking")
	#picks =pick_obj.search(cr,uid,[('origin','=',move.origin)])
	#if not picks:
	picks = pick_obj.search(cr, uid, [('origin','=',move.origin),
				('group_id', '=', move.group_id.id),
				('location_id', '=', move.location_id.id),
				('location_dest_id', '=', move.location_dest_id.id),
				('picking_type_id', '=', move.picking_type_id.id),
				('printed', '=', False),
                		('state', 'in', ['draft', 'confirmed', 'waiting', 'partially_available', 'assigned'])], 
				limit=1, context=context)
		
        if picks:
            pick = picks[0]
        else:
            values = self._prepare_picking_assign(cr, uid, move, context=context)
            pick = pick_obj.create(cr, uid, values, context=context)
        return self.write(cr, uid, move_ids, {'picking_id': pick}, context=context)
    	
